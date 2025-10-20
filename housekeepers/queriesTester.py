#!/usr/local/bin/python3

from bycon import *
from pymongo import MongoClient

from bycon import byconServiceLibs
from service_helpers import assert_single_dataset_or_exit


"""
* ./housekeepers/queriesTester.py -d progenetix --filters "pgx:icdom-81703"
* ./housekeepers/queriesTester.py -d progenetix --mode testqueries
"""

################################################################################
################################################################################
################################################################################

def main():
	ds_id = assert_single_dataset_or_exit()
	target_path_id = "individuals"
	ho_key = f'{target_path_id}.id'
	BYC_PARS.update({"response_entity_path_id": target_path_id})
	ByconEntities().set_entities()

	r_ids = MultiQueryResponses(ds_id).get_individual_ids()

	print(f'{"\n".join(BYC.get("NOTES", []))}')


################################################################################
################################################################################
################################################################################

class MultiQueryResponses:
    def __init__(self, dataset_id=None):
        multiqueries = {"ByconQuery": {}}
        if "testqueries" in BYC_PARS.get("mode", "").lower():
            multiqueries = BYC.get("test_queries")
        self.entity_ids = set()
        self.target_path_id = "biosamples"
        self.multiqueries = multiqueries
        self.ds_id = dataset_id

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_analysis_ids(self):
        self.target_path_id = "analyses"
        self.__run_multi_queries()
        return self.entity_ids


    # -------------------------------------------------------------------------#

    def get_biosample_ids(self):
        self.target_path_id = "biosamples"
        self.__run_multi_queries()
        return self.entity_ids


    # -------------------------------------------------------------------------#

    def get_individual_ids(self):
        self.target_path_id = "individuals"
        self.__run_multi_queries()
        return self.entity_ids


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __run_multi_queries(self):
        ho_id = f'{self.target_path_id}.id'
        for qek, qev in self.multiqueries.items():
            for p, v in qev.items():
                BYC_PARS.update({p: v})
            prjsontrue(qev)
            prjsontrue(BYC_PARS)

            BRS = ByconResultSets()
            ds_results = BRS.datasetsResults()

            # clean out those globals for next run
            for p, v in qev.items():
                BYC_PARS.pop(p)
            
            if not (ds := ds_results.get(self.ds_id)):
                r_c = BRS.get_record_queries()
                BYC["ERRORS"].append(f'ERROR - no {qek} data for {self.ds_id}')
                continue
            f_i_ids = ds[ho_id].get("target_values", [])
            self.entity_ids = set(self.entity_ids)
            self.entity_ids.update(random_samples(f_i_ids, min(BYC_PARS.get("limit", 200), len(f_i_ids))))
            BYC["NOTES"].append(f'{qek} with {ds[ho_id].get("target_count", 0)} {self.target_path_id} hits')
            self.entity_ids = list(self.entity_ids)


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
