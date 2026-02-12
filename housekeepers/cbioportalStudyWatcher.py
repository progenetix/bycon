#!/usr/bin/env python3
"""cBioPortal study watcher

Compare the set of cBioPortal studies **already referenced in Progenetix**
(via `references.cbioportal.id`) against the set of cBioPortal studies that have
**copy-number data** available in cBioPortal.

We track two availability types:
- **CNA molecular profiles** (processed/discrete-level availability check)
- **Copy-number segments** (raw-ish segments availability check via `/copy-number-segments/fetch`)

Outputs a TSV with studies that are present in cBioPortal (with CNV/CNA data) but not yet
referenced in Progenetix.

"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os

import requests
from pymongo import MongoClient


CBIOPORTAL_API_DEFAULT = "https://www.cbioportal.org/api"


@dataclass
class State:
    checked: dict[str, dict[str, Any]]  # studyId -> {has_cna: bool|None, has_segments: bool|None, checked_at: int}


def _now() -> int:
    return int(time.time())


def load_state(path: Path) -> State:
    if not path.exists():
        return State(checked={})
    try:
        data = json.loads(path.read_text())
        checked = data.get("checked", {}) if isinstance(data, dict) else {}
        if not isinstance(checked, dict):
            checked = {}
        return State(checked=checked)
    except Exception:
        return State(checked={})


def save_state(state: State, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"checked": state.checked, "saved_at": _now()}, indent=2))


def normalize_cbioportal_id(x: str) -> str:
    x = str(x).strip()
    if x.lower().startswith("cbioportal:"):
        x = x.split(":", 1)[1]
    return x.strip().lower()


def get_existing_cbioportal_studies_from_mongo(*, mongo_host: str, dataset_id: str) -> set[str]:
   
    mc = MongoClient(host=mongo_host)
    try:
        db = mc[dataset_id]
        # Prefer biosample, fall back to analyses.
        for coll_name in ["biosamples", "analyses"]:
            if coll_name not in db.list_collection_names():
                continue
            coll = db[coll_name]
            vals = coll.distinct("references.cbioportal.id")
            out = set()
            for v in vals:
                if v is None:
                    continue
                if isinstance(v, list):
                    for vv in v:
                        if vv:
                            out.add(normalize_cbioportal_id(vv))
                else:
                    out.add(normalize_cbioportal_id(v))
            out.discard("")
            if out:
                return out
        return set()
    finally:
        mc.close()


def cbioportal_get_studies(api_base: str, *, timeout: int = 60) -> list[str]:
    url = api_base.rstrip("/") + "/studies"
    r = requests.get(url, headers={"Accept": "application/json"}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    study_ids: list[str] = []
    for row in data:
        sid = row.get("studyId") if isinstance(row, dict) else None
        if sid:
            study_ids.append(str(sid))
    return study_ids


def cbioportal_study_has_cna(api_base: str, study_id: str, *, timeout: int = 60) -> bool:
    url = api_base.rstrip("/") + "/molecular-profiles"
    r = requests.get(
        url,
        params={"studyId": study_id},
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    for mp in data:
        if not isinstance(mp, dict):
            continue
        mat = str(mp.get("molecularAlterationType", "")).strip().upper()
        if mat == "COPY_NUMBER_ALTERATION":
            return True
    return False


def cbioportal_get_sample_lists(api_base: str, study_id: str, *, timeout: int = 60) -> list[str]:
    url = api_base.rstrip("/") + "/sample-lists"
    r = requests.get(
        url,
        params={"studyId": study_id, "pageSize": 10000000, "projection": "SUMMARY"},
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    out: list[str] = []
    for row in data:
        if isinstance(row, dict) and row.get("sampleListId"):
            out.append(str(row["sampleListId"]))
    return out


def cbioportal_get_sample_ids_for_list(api_base: str, sample_list_id: str, *, timeout: int = 60) -> list[str]:
    url = api_base.rstrip("/") + f"/sample-lists/{sample_list_id}/sample-ids"
    r = requests.get(url, headers={"Accept": "application/json"}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return [str(x) for x in data if x]


def cbioportal_study_has_segments(api_base: str, study_id: str, *, timeout: int = 60) -> bool:
    """
      1) find a sample list (prefer <studyId>_all)
      2) grab 1 sampleId
      3) POST to /copy-number-segments/fetch

    If return a non-empty result, we treat the study as having segment CNV data.
    """

    sample_lists = cbioportal_get_sample_lists(api_base, study_id, timeout=timeout)
    if not sample_lists:
        return False

    preferred = f"{study_id}_all"
    sample_list_id = preferred if preferred in sample_lists else sample_lists[0]

    sample_ids = cbioportal_get_sample_ids_for_list(api_base, sample_list_id, timeout=timeout)
    if not sample_ids:
        return False

    sample_id = sample_ids[0]

    url = api_base.rstrip("/") + "/copy-number-segments/fetch"
    body = [{"sampleId": sample_id, "studyId": study_id}]
    r = requests.post(
        url,
        params={"projection": "SUMMARY"},
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=body,
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    return bool(data)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Check whether cBioPortal has new CNA studies not yet referenced in our Progenetix/Bycon dataset."
    )
    ap.add_argument("--dataset-id", default="progenetix", help="MongoDB dataset db name (default: progenetix)")
    ap.add_argument("--mongo-host", default="localhost", help="Mongo host (default: localhost or BYCON_MONGO_HOST)")
    ap.add_argument("--cbio-api", default=CBIOPORTAL_API_DEFAULT, help="cBioPortal API base URL")
    ap.add_argument(
        "--state-file",
        default="local/state/cbioportal_study_watcher_state.json",
        help="JSON state cache (default: local/state/...)"
    )
    ap.add_argument(
        "--out-tsv",
        default="local/reports/cbioportal_new_cna_studies.tsv",
        help="Output TSV path (default: local/reports/...)"
    )
    ap.add_argument(
        "--stale-days",
        type=int,
        default=30,
        help="Re-check cBioPortal availability if cached result older than this (default: 30)"
    )
    ap.add_argument(
        "--require-segments",
        action="store_true",
        help="If set, only report studies that have copy-number segments available (raw-ish CNV).",
    )
    ap.add_argument(
        "--max-studies",
        type=int,
        default=0,
        help="Optional limit for number of studies to check (0 = no limit). Useful for quick tests."
    )

    args = ap.parse_args()

    mongo_host = str(args.mongo_host)
    if os.environ.get("BYCON_MONGO_HOST") and (args.mongo_host == "localhost"):
        mongo_host = str(os.environ.get("BYCON_MONGO_HOST"))

    dataset_id = str(args.dataset_id)
    api_base = str(args.cbio_api)

    state_path = Path(args.state_file)
    out_path = Path(args.out_tsv)

    stale_s = int(args.stale_days) * 86400

    try:
        existing = get_existing_cbioportal_studies_from_mongo(mongo_host=mongo_host, dataset_id=dataset_id)
    except Exception as e:
        print(f"[ERROR] Could not read existing cbioportal study ids from Mongo ({mongo_host}/{dataset_id}): {e}", file=sys.stderr)
        raise

    study_ids = cbioportal_get_studies(api_base)
    if int(args.max_studies) and len(study_ids) > int(args.max_studies):
        study_ids = study_ids[: int(args.max_studies)]

    state = load_state(state_path)

    cna_studies: list[str] = []
    seg_studies: list[str] = []
    checked_n = 0
    for sid_raw in study_ids:
        sid = normalize_cbioportal_id(sid_raw)
        if not sid:
            continue

        cached = state.checked.get(sid)
        needs_check = True
        if isinstance(cached, dict):
            ts = int(cached.get("checked_at", 0) or 0)
            if ts and (_now() - ts) < stale_s:
                needs_check = False

        if needs_check:
            try:
                has_cna = bool(cbioportal_study_has_cna(api_base, sid_raw))
            except Exception as e:
                has_cna = None
                err = f"cna:{str(e)[:160]}"
            else:
                err = None

            try:
                has_seg = bool(cbioportal_study_has_segments(api_base, str(sid_raw)))
            except Exception as e:
                has_seg = None
                err2 = f"seg:{str(e)[:160]}"
                err = (err + ";" + err2) if err else err2

            state.checked[sid] = {"has_cna": has_cna, "has_segments": has_seg, "checked_at": _now()}
            if err:
                state.checked[sid]["error"] = err
            checked_n += 1

        cached2 = state.checked.get(sid, {})
        if cached2.get("has_cna") is True:
            cna_studies.append(sid)
        if cached2.get("has_segments") is True:
            seg_studies.append(sid)

    save_state(state, state_path)

    cna_set = set(cna_studies)
    seg_set = set(seg_studies)

    candidate = seg_set if bool(args.require_segments) else cna_set
    new = sorted(list(candidate - set(existing)))

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write TSV
    lines = ["study_id\tis_new\thas_cna\thas_segments\tin_existing\n"]
    for sid in new:
        row = state.checked.get(str(sid), {})
        has_cna = 1 if row.get("has_cna") is True else 0
        has_seg = 1 if row.get("has_segments") is True else 0
        lines.append(f"{sid}\t1\t{has_cna}\t{has_seg}\t0\n")

    out_path.write_text("".join(lines))

    print(f"dataset_id\t{dataset_id}")
    print(f"mongo_host\t{mongo_host}")
    print(f"cbio_api\t{api_base}")
    print(f"existing_studies\t{len(existing)}")
    print(f"cbioportal_total_studies\t{len(study_ids)}")
    print(f"cbioportal_cna_studies\t{len(cna_set)}")
    print(f"cbioportal_segment_studies\t{len(seg_set)}")
    print(f"new_studies_reported\t{len(new)}")
    print(f"checked_this_run\t{checked_n}")
    print(f"state_file\t{state_path}")
    print(f"out_tsv\t{out_path}")


if __name__ == "__main__":
    main()
