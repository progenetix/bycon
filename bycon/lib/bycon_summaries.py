from pymongo import MongoClient

from config import *
from bycon_helpers import *

################################################################################
################################################################################
################################################################################

class ByconSummaries:
    def __init__(self, ds_id=None):
        self.dataset_id = ds_id
        a_d_s = BYC.get("summaries_definitions", {}).get("$defs", {}).values()

        self.summaries = []
        # ordered selection of aggregation concepts
        if len(a_t_s := BYC_PARS.get("aggregation_terms", [])) > 0:
            for a_d_k in a_t_s:
                for a_d in a_d_s:
                    if a_d.get("id") in a_t_s:
                        self.summaries.append(a_d)
                        continue
        else:
            self.summaries = list(a_d_s)

        self.dataset_aggregation = [] 
        self.mongo_client = MongoClient(host=BYC_DBS["mongodb_host"])
        self.data_client = self.mongo_client[ds_id]
        self.term_coll = self.data_client["collations"]


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def datasetResultAggregation(self, dataset_result={}):
        self.dataset_result = dataset_result

        # CAVE: Always aggregating on biosamples
        self.__aggregate_dataset_data(use_dataset_result=True)

        return self.dataset_aggregation


    # -------------------------------------------------------------------------#

    def datasetAllAggregation(self):
        self.__aggregate_dataset_data()
        return self.dataset_aggregation


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __aggregate_dataset_data(self, query={}, use_dataset_result=False):
        # one could aggregate all terms in one pipeline, but this is clearer
        self.aggregation_pre_query = query
        for a_v in self.summaries:
            if use_dataset_result:
                self.__generate_query_from_dataset_result(a_v)
            a_v.update({"distribution": []})    
            self.__aggregate_concepts(a_v)
            self.__reshape_dataset_aggregation()


    # -------------------------------------------------------------------------#

    def __generate_query_from_dataset_result(self, a_v):
        # TODO: Default scope to response entity?
        scope = a_v.get("scope", "biosample")
        coll = BYC_DBS.get(f"{scope}_coll", "___none___")
        # TODO: Fallback query for 0 results?
        if not (coll_k := f"{coll}.id") in self.dataset_result.keys():
            return
        res = self.dataset_result.get(coll_k, {})
        q_v_s = res.get("target_values", [])
        self.aggregation_pre_query = {"id": {"$in": q_v_s}}


    # -------------------------------------------------------------------------#

    def __reshape_dataset_aggregation(self):
        """Post-processing of the aggregation results to remove unneeded keys.
        """
        for i_a, a_v in enumerate(self.dataset_aggregation):
            for i_c, c_v in enumerate(a_v.get("concepts", [])):
                c_v.pop("splits", None)
                c_v.pop("termIds", None)


    # -------------------------------------------------------------------------#

    def __aggregate_concepts(self, a_v):
        if len(concepts := a_v.get("concepts", [])) < 1:
            return
        scopes = set()
        for c in concepts:
            scope, prop = c.get("property", "___none1___.___none1___").split('.', 1)
            scopes.add(scope)
        if len(scopes := list(scopes)) != 1:
            return

        if not (d_c := BYC_DBS.get(f"{scopes[0]}_coll")):
            return
        data_coll = self.data_client[d_c]

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
        if a_v.get("sorted") is True:
            agg_p.append({ "$sort": { "_id.order": 1 } })
        else:
            agg_p.append({ "$sort": { "count": -1 } })

        if len(agg_d := list(data_coll.aggregate(agg_p))) < 1:
            return

        if a_v.get("sorted") is True:
            k = list(agg_d[0]["_id"].keys())[0]
            if "order" in agg_d[0]["_id"][k]:
                agg_d = sorted(agg_d, key=lambda x: x["_id"][k].get("order", 9999))

        # label lookups only for term-based aggregations
        for a in agg_d:
            if not (i_k := a.get("_id")):
                continue
            c_v_s = []
            id_v_s = list(i_k.values())
            for v in id_v_s:
                if type(v) is dict and "id" in v:
                    label = v.get("label", v.get("id"))
                    c_v_s.append({"id": v.get("id"), "label": label})
                    continue
                label = v
                if (coll := self.term_coll.find_one( {"id": v})):
                    label = coll.get("label", label)
                    c_v_s.append({"id": v, "label": label})
                    continue
                c_v_s.append({"id": v, "label": label})

            a_v["distribution"].append({
                "concept_values": c_v_s,
                "count": a.get("count", 0)
            })

        self.dataset_aggregation.append(a_v)


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

        if len(terms := concept.get("termIds", [])) < 1:
            return False

        scope, concept_id = concept.get("property", "___none___.___none___").split('.', 1)

        branches = []
        for d_i, i_k in enumerate(terms):
            if not (coll := self.term_coll.find_one( {"id": i_k})):
                continue
            label = coll.get("label", i_k)
            if len(child_terms := coll.get("child_terms", [])) < 1:
                continue
            branches.append({
                "case": { "$in": [ f'${concept_id}', child_terms ] },
                "then": {"id": i_k, "label": label, "order": d_i}
            })

        # fallback dummy branch - at least one is needed or error
        if len(branches) < 1:
            branches.append({
                "case": { "$in": [f'${concept_id}', [ "___undefined___" ]] },
                "then": {"id": "undefined", "label": "undefined", "order": 1}
            })

        _id = {
            "$switch": {
                "branches": branches,
                "default": {"id": "other", "label": "other", "order": len(terms)}
            }
        }

        return _id


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

        f = concept.get('format', "")

        split_labs = splits
        split_vals = splits
        branches = []

        if "iso8601duration" in f:
            concept_id = f"{concept_id}_days"
            split_labs = ["unknown"]
            split_vals = [0]
            pre = "P0D"
            for l in splits:
                if re.match(r"^P\d", str(l)):
                    if int(d := days_from_iso8601duration(l)) > 0:
                        split_labs.append(f"[{pre}, {l})")
                        split_vals.append(d)
                    pre = l

        for d_i, d_l in enumerate(split_labs):
            branches.append({
                "case": { "$lt": [ f'${concept_id}', split_vals[d_i] ] },
                "then": {"id": d_l, "label": d_l, "order": d_i}
            })

        _id = {
            "$switch": {
                "branches": branches,
                "default": {"id": "other", "label": "other", "order": len(split_labs)}
            }
        }

        # prdbug(_id)

        return _id

