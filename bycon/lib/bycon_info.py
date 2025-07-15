from isodate import date_isoformat
from pymongo import MongoClient
from progress.bar import Bar

from bycon_helpers import *
from config import *
from parameter_parsing import ByconDatasets

class ByconInfo():
    def __init__(self, distvars=True):
        self.count_distvars = distvars
        self.database_names = ByconDatasets().get_database_names()
        self.mongo_client = MongoClient(host=DB_MONGOHOST)
        self.info_coll = self.mongo_client[ HOUSEKEEPING_DB ][ HOUSEKEEPING_INFO_COLL ]
        self.dataset_ids = list(BYC["dataset_definitions"].keys())
        self.data_colls = ["biosamples", "individuals", "variants", "analyses"]
        self.today = date_isoformat(datetime.now())
        self.status = {"date": self.today}


    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def update_beaconinfo(self):
        self.__assess_datasets()
        self.info_coll.delete_many({"date": self.today})
        if not BYC["TEST_MODE"]:
            self.info_coll.insert_one(self.status)
            print(f'\n{self.__hl()}==> updated entry {self.status["date"]} in {HOUSEKEEPING_DB}.{HOUSEKEEPING_INFO_COLL}')
        else:
            print(f'\n{self.__hl()}==> no {HOUSEKEEPING_DB}.{HOUSEKEEPING_INFO_COLL} update since in TEST_MODE')


    #--------------------------------------------------------------------------#

    def beaconinfo_get_latest(self):
        return self.info_coll.find( { }, { "_id": 0 } ).sort( {"date": -1} ).limit( 1 )

    #--------------------------------------------------------------------------#
    #----------------------------- Private ------------------------------------#
    #--------------------------------------------------------------------------#

    def __assess_datasets(self):
        self.status.update({"datasets": {}})
        for ds_id in list(set(self.dataset_ids) & set(self.database_names)):
            self.__dataset_update_counts(ds_id)

    #--------------------------------------------------------------------------#

    def __dataset_update_counts(self, ds_id):
        ds_db = self.mongo_client[ds_id]
        b_i_ds = {
            "counts": {},
            "collation_types": {},
            "collations": {},
            "updated": datetime.now().isoformat()
        }
        c_n = ds_db.list_collection_names()
        for c in self.data_colls:
            if c not in c_n:
                continue

            no = ds_db[ c ].estimated_document_count()
            b_i_ds["counts"].update( { c: no } )
            if c == "variants" and self.count_distvars:
                v_d = { }
                bar = Bar(ds_id+' variants', max = no, suffix='%(percent)d%%'+" of "+str(no) )
                for v in ds_db[ c ].find({ "variant_internal_id": {"$exists": True }}):
                    v_d[ v["variant_internal_id"] ] = 1
                    bar.next()
                bar.finish()
                b_i_ds["counts"].update( { "variants_distinct": len(v_d.keys()) } )

        coll_types = ds_db["collations"].distinct("collation_type", {"code_matches": {"$gt": 0}})
        pipeline = [
            {"$group": {"_id": "$collation_type", "count": {"$sum": 1}}}
        ]
        for ct in list(ds_db["collations"].aggregate(pipeline)):
            b_i_ds["collation_types"].update({ct["_id"]: ct["count"]})
        for ctk in b_i_ds["collation_types"].keys():
            for coll in ds_db["collations"].find(
                {"collation_type": ctk, "code_matches": {"$gt": 0}},
                {"_id": 0, "id": 1, "entity": 1, "db_key": 1, "label": 1, "collation_type": 1, "code_matches": 1}
            ):
                cid = coll.pop("id", "___none___")
                b_i_ds["collations"].update({cid: coll})

        if not BYC["TEST_MODE"]:
            self.status["datasets"].update({ds_id: b_i_ds})
        else:
            prjsonnice(b_i_ds)

#--------------------------------------------------------------------------#

    def __hl(self):
        return "".join(["#"] * 80) + "\n"

