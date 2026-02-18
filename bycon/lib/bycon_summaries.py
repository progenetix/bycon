import re

from config import BYC, BYC_DBS, BYC_PARS
from bycon_helpers import ByconMongo, days_from_iso8601duration, prdbug

################################################################################
################################################################################
################################################################################

class ByconSummaries:
    def __init__(self, ds_id=None):
        self.dataset_id = ds_id
        self.summaries = []

        a_d_s = BYC.get("aggregation_terms", {}).get("defaults", [])
        a_c_s = BYC.get("aggregation_terms", {}).get("$defs", {})
        a_t_s = BYC_PARS.get("aggregators", [])

        # construct the aggregations from concepts and combinations
        # this might be transitional, e.g. when BYC_PARS["aggregators"]
        # is replaced (`aggregationConceptIds` arrays or such)
        if len(a_t_s) < 1:
            a_t_s = a_d_s

        # WiP: construct terms from aggregators
        if len(a_t_s) > 0:
            for a in a_t_s:
                t_a = []
                if not isinstance(a, list):
                    for a_id in re.split("::", a):
                        t_a.append(a_id)
                else:
                    for a_o in a:
                        if (a_id := a_o.get("id")):
                            t_a.append(a_id)

                if len(t_a) < 1:
                    continue
                concepts    = []
                labels      = []
                ids         = []
                for a_id in t_a:
                    if (c := a_c_s.get(a_id)):
                        concepts.append(c)
                        ids.append(a_id)
                        if (lab := c.get("label")):
                            labels.append(lab)

                if len(concepts) == len(t_a):
                    self.summaries.append(
                        {
                            "id": "::".join(ids),
                            "concepts": concepts,
                            "label": " by ".join(labels),
                            "scope": concepts[0].get("scope", "biosample")
                        }
                    )

        self.dataset_summaries  = [] 
        self.data_client        = ByconMongo(ds_id).openMongoDatabase()
        self.term_coll          = ByconMongo(ds_id).openMongoColl("collations")


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def datasetResultSummaries(self, dataset_result={}):
        self.dataset_result = dataset_result

        # CAVE: Always aggregating on biosamples
        self.__summarize_dataset_data(use_dataset_result=True)

        return self.dataset_summaries


    # -------------------------------------------------------------------------#

    def datasetAllSummaries(self):
        self.__summarize_dataset_data()
        return self.dataset_summaries


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __summarize_dataset_data(self, query={}, use_dataset_result=False):
        # one could aggregate all terms in one pipeline, but this is clearer
        self.aggregation_pre_query = query
        for a_v in self.summaries:
            if use_dataset_result:
                self.__generate_query_from_dataset_result(a_v)
            a_v.update({"distribution": []})
            try:
                self.__summarize_concepts(a_v)
            except Exception as e:
                prdbug(f"Exception at __summarize_concepts: {e}")
                BYC["ERRORS"].append(e)
            try:
                self.__reshape_dataset_summaries()
            except Exception as e:
                prdbug(f"Exception at __reshape_dataset_summaries:{e}")
                BYC["ERRORS"].append(e)


    # -------------------------------------------------------------------------#

    def __generate_query_from_dataset_result(self, a_v):
        # TODO: Default scope to response entity?
        scope = a_v.get("scope", "biosample")
        coll = BYC_DBS.get("collections", {}).get(scope, "___none___")
        # TODO: Fallback query for 0 results?
        if (coll_k := f"{coll}.id") not in self.dataset_result.keys():
            return
        res = self.dataset_result.get(coll_k, {})
        q_v_s = res.get("target_values", [])
        self.aggregation_pre_query = {"id": {"$in": q_v_s}}


    # -------------------------------------------------------------------------#

    def __reshape_dataset_summaries(self):
        """Post-processing of the aggregation results to remove unnecessary keys.
        """
        return
        # for i_a, a_v in enumerate(self.dataset_summaries):
        #     for i_c, c_v in enumerate(a_v.get("concepts", [])):
        #         c_v.pop("splits", None)
        #         c_v.pop("terms", None)


    # -------------------------------------------------------------------------#

    def __summarize_concepts(self, a_v):
        if len(concepts := a_v.get("concepts", [])) < 1:
            return
        scopes = set()
        for c in concepts:
            scope, prop = c.get("property", "___none1___.___none1___").split('.', 1)
            scopes.add(scope)
        if len(scopes := list(scopes)) != 1:
            return

        if not (m_c := BYC_DBS.get("collections", {}).get(scopes[0])):
            return
        data_coll = self.data_client[m_c]

        _id = {}
        for c in concepts:
            scope, concept_id = c.get("property", "___none___.___none___").split('.', 1)
            c_id = concept_id.replace(".", "_")
            _id.update({c_id: self.__id_object(c)})

        agg_p = [{ "$match": self.aggregation_pre_query }]
        agg_p.append(
            { "$group":
                {
                    "_id": _id,
                    "count": { "$sum": 1 }
                }
            }
        )
        # sorting either on logical order () detection order
        prdbug(f"... concept {concepts[0].get("id")} sorted?: {concepts[0].get("sorted")}")
        if concepts[0].get("sorted") is True:
            agg_p.append({ "$sort": { "_id.order": 1 } })
            a_v.update({"sorted": True})
        else:
            agg_p.append({ "$sort": { "count": -1 } })

        if len(agg_d := list(data_coll.aggregate(agg_p))) < 1:
            return

        if concepts[0].get("sorted") is True:
            k = list(agg_d[0]["_id"].keys())[0]
            if type(d := agg_d[0]["_id"].get(k)) is dict:
                if "order" in d.keys():
                    agg_d = sorted(agg_d, key=lambda x: x["_id"][k].get("order", 9999))

        # label lookups only for term-based aggregations
        for a in agg_d:
            if not (i_k := a.get("_id")):
                continue
            c_v_s = []
            if not i_k.values():
                id_v_s = ["Undefined"]
            else:
                id_v_s = list(i_k.values())

            # adding undefined for second category if missing
            # TODO: Check if it is really only the 2nd category that might be missing...
            while len(id_v_s) < len(concepts):
                id_v_s.append({"id": "undefined", "label": "undefined"})
            
            for v in id_v_s:
                if type(v) is dict and "id" in v:
                    label = str(v.get("label", v.get("id")))
                    c_v_s.append({"id": str(v.get("id")), "label": label})
                    continue
                label = str(v)
                if (coll := self.term_coll.find_one( {"id": v})):
                    label = str(coll.get("label", label))
                    c_v_s.append({"id": str(v), "label": label})
                    continue
                c_v_s.append({"id": str(v), "label": label})

            include = True
            for c in c_v_s:
                if str(c.get("id")) == "NO_MATCH":
                    include = False
            if include is True:
                a_v["distribution"].append({
                    "concept_values": c_v_s,
                    "count": a.get("count", 0)
                })

        if len(a_v.get("distribution", [])) > 0:
            self.dataset_summaries.append(a_v)


    # -------------------------------------------------------------------------#

    def __id_object(self, concept):
        if (_id := self.__switch_branches_from_terms(concept)):
            return _id
        if (_id := self.__switch_branches_from_splits(concept)):
            return _id
        scope, concept_id = concept.get("property", "___none___.___none___").split('.', 1)
        return f"${concept_id}"


    # -------------------------------------------------------------------------#

    def __switch_branches_from_terms(self, concept):
        """
        Switch example for term list from children... 

        Note: https://www.mongodb.com/docs/manual/reference/operator/aggregation/switch/
        ```
        db.biosamples.aggregate([
            { $group: {
                "_id": {
                    "cancerType": {
                        $switch: {
                            "branches": [
                                { "case": { $in: [ "$histological_diagnosis.id", ["NCIT:C3466", "NCIT:C3457", "NCIT:C3163"] ]}, "then": {"id": "...", "label": "Some Lymphoma"} },
                                { "case": { $in: [ "$histological_diagnosis.id", ["NCIT:C3512", "NCIT:C3493"] ]}, "then": {"id": "...", "label": "Some Lung Cancer"} }
                            ],
                            "default": {"id": "other", "label": "other"}
                        }
                    }
                },
                "count": { $sum: 1 }
            }}
        ])
        ```
        """

        if len(terms := concept.get("terms", [])) < 1:
            return False

        scope, concept_id = concept.get("property", "___none___.___none___").split('.', 1)

        branches = []
        for d_i, t in enumerate(terms):
            t_id    = t.get("id", "___none___") 
            t_label = t.get("label", t_id) 
            if not (coll := self.term_coll.find_one( {"id": t_id} )):
                continue
            if len(child_terms := coll.get("child_terms", [])) < 1:
                continue
            branches.append({
                "case": { "$in": [ f'${concept_id}', child_terms ] },
                "then": { "id": t_id, "label": t_label, "order": d_i }
            })

        # fallback dummy branch - at least one is needed or error
        if len(branches) < 1:
            branches.append({
                "case": { "$in": [f'${concept_id}', [ "___undefined___" ]] },
                "then": {"id": "undefined", "label": "undefined", "order": 1}
            })

        return {
            "$switch": {
                "branches": branches,
                "default": {"id": "NO_MATCH", "label": "other", "order": len(terms)}
            }
        }

    # -------------------------------------------------------------------------#

    def __switch_branches_from_splits(self, concept):
        """
        Numeric splits can be implemented using `$bucket` or `$switch`. We're
        preferimg switches since they can be combined with other aggregators.

        Switch example for age at diagnosis buckets:

        ```
        db.biosamples.aggregate([
            { $group: {
                "_id": {
                    "ageAtDiagnosis": {
                        $switch: {
                            "branches": [
                                { "case": { $lt: [ "$individual_info.index_disease.onset.age_days", 365 ] }, "then": "<P1Y" },
                                { "case": { $lt: [ "$individual_info.index_disease.onset.age_days", 1825 ] }, "then": "<P5Y" },
=                               { "case": { $lt: [ "$individual_info.index_disease.onset.age_days", 14600 ] }, "then": "<P40Y" }
                            ],
                            "default": "undefined"
                        }
                    }
                },
                "count": { $sum: 1 }
            }}
        ])
        ```
        """

        if len(splits := concept.get("splits", [])) < 1:
            return False

        scope, concept_id = concept.get("property", "___none___.___none___").split('.', 1)

        split_labs  = list(x.get("label", x.get("value", "undefined")) for x in splits)
        split_vals  = list(x.get("value", "undefined") for x in splits)
        split_ids   = split_vals

        branches    = []

        if "iso8601duration" in str(concept.get('format', "")):
            pre         = "undefined"
            concept_id  = f"{concept_id}_days"
            split_vals  = [0]
            split_l     = [pre]
            split_ids   = [pre]
            for i, l in enumerate(splits):
                l = l.get("value")
                if re.match(r"^P\d", str(l)):
                    if int(d := days_from_iso8601duration(l)) > 0:
                        # split_l.append(f"[{pre}, {l})")
                        split_l.append(split_labs[i])
                        split_vals.append(d)
                        split_ids.append(f"<{re.sub("P", "", l).lower()}")
                    pre = l
            split_labs = split_l

        for d_i, d_l in enumerate(split_labs):
            branches.append({
                "case": { "$lt": [ f'${concept_id}', split_vals[d_i] ] },
                "then": {"id": split_ids[d_i], "label": d_l, "order": d_i}
            })

        _id = {
            "$switch": {
                "branches": branches,
                "default": {"id": "other", "label": "other", "order": len(split_labs)}
            }
        }

        return _id

