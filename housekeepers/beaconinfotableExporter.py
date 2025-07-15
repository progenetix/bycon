#!/usr/local/bin/python3

from os import mkdir, path

from bycon import ByconInfo, HOSTNAME
from byconServiceLibs import (
	assert_single_dataset_or_exit,
	log_path_root,
	write_log
)

ds_id = assert_single_dataset_or_exit()

print(f'==> Using statistics from {ds_id}')

stat = list(ByconInfo().beaconinfo_get_latest())[0]

log_dir = path.join(log_path_root(), f'{stat["date"]}-{ds_id}-{HOSTNAME}')
if not path.exists(log_dir):
    mkdir(log_dir)

lines = []
for k, v in stat["datasets"][ds_id]["counts"].items():
	lines.append(f'{k}\t{v}')
fp = path.join( log_dir, f'counts.tsv' )
write_log(lines, fp, "")

lines = []
for k, v in stat["datasets"][ds_id]["collations"].items():
	lines.append(f'{k}\t{v.get("label", "")}\t{v.get("entity", "")}\t{v.get("code_matches", "")}\t{v.get("collation_type", "")}\t{v.get("db_key", "")}')
fp = path.join( log_dir, f'collations.tsv' )
write_log(lines, fp, "")

lines = []
for k, v in stat["datasets"][ds_id]["collation_types"].items():
	lines.append(f'{k}\t{v}')
fp = path.join( log_dir, f'collation_types.tsv' )
write_log(lines, fp, "")

