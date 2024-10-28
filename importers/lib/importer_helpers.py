import datetime
from os import path
from progress.bar import Bar
from pymongo import MongoClient
from random import sample as random_samples

# bycon
from config import *
from bycon_helpers import prjsonnice, prdbug
from variant_mapping import ByconVariant

from byconServiceLibs import assertSingleDatasetOrExit, ByconBundler, import_datatable_dict_line, write_log

################################################################################
################################################################################
################################################################################

class ByconautImporter():
    def __init__(self, use_file=True):
        self.log = []
        self.entity = None
        self.dataset_id = BYC["BYC_DATASET_IDS"][0]
        self.limit = BYC_PARS.get("limit", 0)
        self.input_file = None
        self.import_collname = None
        self.import_entity = None
        self.import_id = None
        self.use_file = use_file
        self.input_file = None
        self.output_dir = None
        self.upstream = ["individuals", "biosamples", "analyses"]
        self.downstream = []
        self.downstream_only = False
        self.mongo_client = MongoClient(host=DB_MONGOHOST)
        self.ind_coll = mongo_client[ self.dataset_id ]["individuals"]
        self.bios_coll = mongo_client[ self.dataset_id ]["biosamples"]
        self.ana_coll = mongo_client[ self.dataset_id ]["analyses"]
        self.target_db = "___none___"
        self.allow_duplicates = False

        self.__initialize_importer()


    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def get_dataset_id(self):
        return self.dataset_id


    #--------------------------------------------------------------------------#

    def get_input_file(self):
        return self.input_file


    #--------------------------------------------------------------------------#

    def import_individuals(self):
        self.__prepare_individuals()
        self.__insert_database_records_from_file()


    #--------------------------------------------------------------------------#

    def update_individuals(self):
        self.__prepare_individuals()
        self.__update_database_records_from_file()


    #--------------------------------------------------------------------------#

    def import_biosamples(self):
        self.__prepare_biosamples()
        self.__insert_database_records_from_file()


    #--------------------------------------------------------------------------#

    def update_biosamples(self):
        self.__prepare_biosamples()
        self.__update_database_records_from_file()


    #--------------------------------------------------------------------------#

    def import_analyses(self):
        self.__prepare_analyses()
        self.__insert_database_records_from_file()


    #--------------------------------------------------------------------------#

    def update_analyses(self):
        self.__prepare_analyses()
        self.__update_database_records_from_file()


    #--------------------------------------------------------------------------#

    def delete_individuals(self):
        self.__prepare_individuals()
        self.__delete_database_records()


    #--------------------------------------------------------------------------#

    def delete_individuals_and_downstream(self):
        self.__prepare_individuals()
        self.downstream = ["biosamples", "analyses", "variants"]
        self.__delete_database_records()


    #--------------------------------------------------------------------------#

    def delete_biosamples(self):
        self.__prepare_biosamples()
        self.__delete_database_records()


    #--------------------------------------------------------------------------#

    def delete_biosamples_and_downstream(self):
        self.__prepare_biosamples()
        self.downstream = ["analyses", "variants"]
        self.__delete_database_records()


    #--------------------------------------------------------------------------#

    def delete_analyses(self):
        self.__prepare_analyses()
        self.__delete_database_records()


    #--------------------------------------------------------------------------#

    def delete_analyses_and_downstream(self):
        self.__prepare_analyses()
        self.downstream = ["variants"]
        self.__delete_database_records()


    #--------------------------------------------------------------------------#

    def delete_variants_of_analyses(self):
        self.__prepare_analyses()
        self.downstream = ["variants"]
        self.downstream_only = True
        self.__delete_database_records()


    #--------------------------------------------------------------------------#

    def import_variants(self):
        self.__prepare_variants()
        self.__insert_variant_records_from_file()


    #--------------------------------------------------------------------------#

    def move_individuals_and_downstream(self):
        self.__prepare_individuals()
        self.target_db = BYC_PARS.get("output", "___none___")
        self.downstream = ["biosamples", "analyses", "variants"]
        self.__move_database_records()


    #--------------------------------------------------------------------------#

    def move_individuals_and_downstream_from_ds_results(self, dataset_results={}):
        self.__prepare_individuals()

        self.target_db = BYC_PARS.get("output", "___none___")
        self.downstream = ["biosamples", "analyses", "variants"]
        iid = self.import_id

        if not (ds := dataset_results.get(self.dataset_id)):
            return

        ind_ids = ds["individuals.id"].get("target_values", [])

        if self.limit > 0:
            if len(ind_ids) > self.limit:
                ind_ids = random_samples(ind_ids, self.limit)

        self.import_docs = []
        for ind_id in ind_ids:
            self.import_docs.append({iid: ind_id})

        self.__move_database_records()


    #--------------------------------------------------------------------------#

    def export_database_from_ids(self):
        if not self.output_dir:
            print("No output directory `--outputdir` specified => quitting ...")
            exit()

        self.__prepare_individuals()
        # TODO: Use some default nanme but check for existence and offer deletion
        self.target_db = BYC_PARS.get("output", f'tmpdb_{datetime.datetime.now().isoformat()}')
        self.downstream = ["biosamples", "analyses", "variants"]

        if self.target_db in BYC["DATABASE_NAMES"]:
            print(f'¡¡¡ You cannot export using an existing database name !!!')
            exit()

        self.mongo_client[self.target_db].drop()
        self.__move_database_records()
        self.__export_database()
        return self.target_db


    #--------------------------------------------------------------------------#
    #----------------------------- Private ------------------------------------#
    #--------------------------------------------------------------------------#

    def __initialize_importer(self):
        BYC.update({"BYC_DATASET_IDS": BYC_PARS.get("dataset_ids", [])})
        self.dataset_id = assertSingleDatasetOrExit()
        if self.use_file:
            self.input_file = BYC_PARS.get("inputfile")
            if not self.input_file:
                print("No input file file specified (-i, --inputfile) => quitting ...")
                exit()
        if not BYC["TEST_MODE"]:
            tmi = input("Do you want to run in TEST MODE (i.e. no database insertions/updates)?\n(Y|n): ")
            if not "n" in tmi.lower():
                BYC.update({"TEST_MODE": True})
        if BYC["TEST_MODE"]:
                print("... running in TEST MODE")

        return


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __prepare_individuals(self):
        # TODO: have those parameters read from bycon globals
        self.import_collname = "individuals"
        self.import_entity = "individual"
        self.import_id = "individual_id"
        self.upstream = []
        self.__check_dataset()
        self.__read_data_file()


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __prepare_biosamples(self):
        # TODO: have those parameters read from bycon globals
        self.import_collname = "biosamples"
        self.import_entity = "biosample"
        self.import_id = "biosample_id"
        self.upstream = ["individuals"]
        self.__check_dataset()
        self.__read_data_file()


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __prepare_analyses(self):
        # TODO: have those parameters read from bycon globals
        self.import_collname = "analyses"
        self.import_entity = "analysis"
        self.import_id = "analysis_id"
        self.upstream = ["individuals", "biosamples"]
        self.__check_dataset()
        self.__read_data_file()


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __prepare_variants(self):
        # TODO: have those parameters read from bycon globals
        self.import_collname = "variants"
        self.import_entity = "genomicVariant"
        self.import_id = "analysis_id"
        self.upstream = ["individuals", "biosamples", "analyses"]
        self.allow_duplicates = True
        self.__check_dataset()
        self.__read_data_file()


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __check_dataset(self):
        # done after assignment of import_collname
        if self.dataset_id not in BYC.get("DATABASE_NAMES",[]):
            print(f'Dataset {self.dataset_id} does not exist. You have to create it first.')
            if "individuals" in str(self.import_collname):
                proceed = input(f'Please type the name of the dataset and hit Enter: ')
                if not str(self.dataset_id) in proceed:
                    exit()
            else:
                exit()


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __read_data_file(self):
        if not self.use_file:
            return
        iid = self.import_id

        bb = ByconBundler()
        self.data_in = bb.read_pgx_file(self.input_file)
        print(f'=> The input file contains {len(self.data_in.data)} items')

        self.import_docs = []

        import_ids = []
        l_no = 0
        for new_doc in self.data_in.data:
            l_no += 1
            if not (import_id_v := new_doc.get(iid)):
                self.log.append(f'¡¡¡ no {iid} value in entry {l_no} => skipping !!!')
                continue
            if import_id_v in import_ids and not self.allow_duplicates:
                self.log.append(f'¡¡¡ duplicated {iid} value in entry {l_no} => skipping !!!')
                continue

            import_ids.append(import_id_v)
            self.import_docs.append(dict(new_doc))


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __export_database(self):
        tds_id = self.target_db
        db_odir = self.output_dir

        e_ds_dir = Path( path.join( db_odir, tds_id ) )
        e_ds_archive = f'{db}.tar.gz'
        system(f'mongodump --db {db} --out {mongo_dir}')
        system(f'cd {mongo_dir} && tar -czf {e_ds_archive} {db} && rm -rf {db}')


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __move_database_records(self):
        ds_id = self.dataset_id
        tds_id = self.target_db
        icn = self.import_collname
        dcs = self.downstream
        ucs = self.upstream
        iid = self.import_id

        if tds_id not in BYC["DATABASE_NAMES"]:
            print(f'¡¡¡ No existing target database defined using `--output` !!!')
            exit()

        source_coll = self.mongo_client[ds_id][icn]
        target_coll = self.mongo_client[tds_id][icn]

        #----------------------- Checking database content --------------------#

        source_ids = []
        for test_doc in self.import_docs:
            s_id_v = test_doc[iid]
            if not source_coll.find_one({"id": s_id_v}):
                self.log.append(f'id {s_id_v} does not exist in {ds_id}.{icn} => maybe deleted already ...')
            else:
                source_ids.append(s_id_v)

        self.__parse_log()

        #---------------------------- Mover Stage -----------------------------#

        # the `target_coll.insert_one({"id": "___init___"})` serves to initialize
        # the target collection and to avoid the need for a separate check for
        # the existence of the target collection
        mov_nos = {icn: 0}
        if not BYC["TEST_MODE"]:
            bar = Bar("Moving ", max = len(source_ids), suffix='%(percent)d%%'+f' of {str(len(source_ids))} {icn}' )
            target_coll.insert_one({"id": "___init___"})
        for m_id in source_ids:
            d_c = source_coll.count_documents({"id": m_id})
            t_c = target_coll.count_documents({"id": m_id})
            if d_c > 0 and t_c < 1:
                mov_nos[icn] += d_c
                if not BYC["TEST_MODE"]:
                    s = source_coll.find_one({"id": m_id})
                    t = target_coll.insert_one(s)
            if not BYC["TEST_MODE"]:
                bar.next()
        if not BYC["TEST_MODE"]:
            target_coll.delete_one({"id": "___init___"})
            bar.finish()

        for c in dcs:
            source_coll = self.mongo_client[ds_id][c]
            target_coll = self.mongo_client[tds_id][c]
            if not BYC["TEST_MODE"]:
                target_coll.insert_one({"id": "___init___"})
                bar = Bar(f'Moving {c} ', max = len(source_ids), suffix='%(percent)d%%'+f' of {str(len(source_ids))} {icn}' )
            mov_nos.update({c: 0})
            for m_id in source_ids:
                d_c = source_coll.count_documents({iid: m_id})
                if d_c > 0:
                    mov_nos[c] += d_c
                    if not BYC["TEST_MODE"]:
                        target_coll.delete_many({iid: m_id})
                        for s in source_coll.find({iid: m_id}):
                            t = target_coll.insert_one(s)
                if not BYC["TEST_MODE"]:
                    bar.next()
            if not BYC["TEST_MODE"]:
                target_coll.delete_one({"id": "___init___"})
                bar.finish()

        if not BYC["TEST_MODE"]:
            for k, v in mov_nos.items():
                print(f'==> moved {v} {k} from {ds_id} to {tds_id}')
        else:
            for k, v in mov_nos.items():
                print(f'==> would have moved {v} {k} from {ds_id} to {tds_id}')


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __delete_database_records(self):
        ds_id = self.dataset_id
        icn = self.import_collname
        dcs = self.downstream
        iid = self.import_id
        fn = self.data_in.fieldnames

        del_coll = self.mongo_client[ds_id][icn]

        #----------------------- Checking database content --------------------#

        del_ids = set()
        for test_doc in self.import_docs:
            del_id_v = test_doc[iid]
            if not del_coll.find_one({"id": del_id_v}):
                self.log.append(f'id {del_id_v} does not exist in {ds_id}.{icn} => maybe deleted already ...')
            del_ids.add(del_id_v)

        self.__parse_log()

        #---------------------------- Delete Stage ----------------------------#

        del_nos = { icn: 0 }
        if not self.downstream_only:
            bar = Bar("Deleting ", max = len(del_ids), suffix='%(percent)d%%'+f' of {str(len(del_ids))} {icn}' ) if not BYC["TEST_MODE"] else False
            for del_id in del_ids:
                d_c = del_coll.count_documents({"id": del_id})
                del_nos[icn] += d_c
                if not BYC["TEST_MODE"]:
                    del_coll.delete_many({"id": del_id})
                    bar.next()
            if not BYC["TEST_MODE"]:
                bar.finish()

        for c in dcs:
            bar = Bar(f'Deleting {c} ', max = len(del_ids), suffix='%(percent)d%%'+f' of {str(len(del_ids))} {icn}' ) if not BYC["TEST_MODE"] else False
            del_coll = self.mongo_client[ds_id][c]
            del_nos.update({c: 0})
            for del_id in del_ids:
                d_c = del_coll.count_documents({iid: del_id})
                del_nos[c] += d_c
                if not BYC["TEST_MODE"]:
                    del_coll.delete_many({iid: del_id})
                    bar.next()
            if not BYC["TEST_MODE"]:
                bar.finish()

        if not BYC["TEST_MODE"]:
            for k, v in del_nos.items():
                print(f'==> deleted {v} {k}')
        else:
            for k, v in del_nos.items():
                print(f'==> would have deleted {v} {k}')
               

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __update_database_records_from_file(self):
        ds_id = self.dataset_id
        icn = self.import_collname 
        ien = self.import_entity
        iid = self.import_id
        fn = self.data_in.fieldnames
        
        import_coll = self.mongo_client[ ds_id ][icn]

        #----------------------- Checking database content --------------------# 

        checked_docs = []
        for test_doc in self.import_docs:
            import_id_v = test_doc[iid]
            self.__check_upstream_ids(test_doc)
            if not import_coll.find_one({"id": import_id_v}):
                self.log.append(f'id {import_id_v} does not exist in {ds_id}.{icn} => you might need to run an importer ...')
                continue
            checked_docs.append(test_doc)

        self.__parse_log()

        #---------------------- Updating checked records-----------------------# 

        bar = Bar("Processing ", max = len(checked_docs), suffix='%(percent)d%%'+" of "+str(len(checked_docs)) ) if not BYC["TEST_MODE"] else False

        #---------------------------- Import Stage ----------------------------# 

        i_no = 0
        for new_doc in checked_docs:
            o_id = new_doc[iid]
            update_i = import_coll.find_one({"id": o_id})
            update_i = import_datatable_dict_line(update_i, fn, new_doc, ien)
            update_i.update({"updated": datetime.datetime.now().isoformat()})

            if not BYC["TEST_MODE"]:
                import_coll.update_one({"id": o_id}, {"$set": update_i})
                bar.next()
            else:
                prjsonnice(update_i)
            i_no += 1

        #---------------------------- Summary ---------------------------------#

        if not BYC["TEST_MODE"]:
            bar.finish()
            print(f'==> updated {i_no} {ien}')
        else:
            print(f'==> tested {i_no} {ien}')


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __insert_database_records_from_file(self):
        ds_id = self.dataset_id
        icn = self.import_collname 
        ien = self.import_entity
        iid = self.import_id
        fn = self.data_in.fieldnames

        import_coll = self.mongo_client[ ds_id ][icn]

        #----------------------- Checking database content --------------------# 

        checked_docs = []
        for test_doc in self.import_docs:
            import_id_v = test_doc[iid]
            self.__check_upstream_ids(test_doc)
            if import_coll.find_one({"id": import_id_v}):
                self.log.append(f'existing id {import_id_v} in {ds_id}.{icn} => please check or remove')
                continue
            checked_docs.append(test_doc)

        self.__parse_log()

        #---------------------------- Import Stage ----------------------------# 

        i_no = 0
        for new_doc in checked_docs:
            update_i = {"id": new_doc[iid]}
            update_i = import_datatable_dict_line(update_i, fn, new_doc, ien)
            update_i.update({"updated": datetime.datetime.now().isoformat()})

            if not BYC["TEST_MODE"]:
                import_coll.insert_one(update_i)
                i_no += 1
            else:
                prjsonnice(update_i)

        #-------------------------------- Summary -----------------------------#

        print(f'=> {i_no} records were inserted into {ds_id}.{icn}')

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __insert_variant_records_from_file(self):
        ds_id = self.dataset_id
        icn = self.import_collname 
        ien = self.import_entity
        iid = self.import_id
        fn = self.data_in.fieldnames

        import_coll = self.mongo_client[ ds_id ][icn]

        delMatchedVars = "y"
        if not BYC["TEST_MODE"]:
            delMatchedVars = input(f'Delete the variants of the same analysis ids as in the input file?\n(Y|n): ')

        #----------------------- Checking database content --------------------# 

        for test_doc in self.import_docs:
            self.__check_upstream_ids(test_doc)
        self.__parse_log()

        #---------------------------- Delete Stage ----------------------------#

        ana_del_ids = set()
        import_vars = []
        for v in self.import_docs:
            if not (vs_id := v.get("variant_state_id")):
                print(f"¡¡¡ The `variant_state_id` parameter is required for variant assignment  line {c}!!!")
                exit()
            if not (ana_id := v.get("analysis_id")):
                print(f"¡¡¡ The `analysis_id` parameter is required for variant assignment  line {c}!!!")
                exit()
            if not "n" in delMatchedVars.lower():
                ana_del_ids.add(ana_id)
            if not "delete" in vs_id.lower():
                import_vars.append(v)

        for ana_id in ana_del_ids:
            v_dels = import_coll.delete_many({"analysis_id": ana_id})
            print(f'==>> deleted {v_dels.deleted_count} variants from {ana_id}')

        #---------------------------- Import Stage ----------------------------# 

        i_no = 0
        for new_doc in import_vars:
            insert_v = import_datatable_dict_line({}, fn, new_doc, ien)
            insert_v = ByconVariant().pgxVariant(insert_v)
            insert_v.update({"updated": datetime.datetime.now().isoformat()})

            if not BYC["TEST_MODE"]:
                vid = import_coll.insert_one(insert_v).inserted_id
                vstr = f'pgxvar-{vid}'
                import_coll.update_one({'_id': vid}, {'$set': {'id': vstr}})
                i_no += 1
            else:
                prjsonnice(insert_v)

        #-------------------------------- Summary -----------------------------#

        print(f'=> {i_no} records were inserted into {ds_id}.{icn}')


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __check_upstream_ids(self, new_doc):
        ind_id = new_doc.get("individual_id", "___none___")
        bios_id = new_doc.get("biosample_id", "___none___")
        ana_id = new_doc.get("analysis_id", "___none___")
        ien = self.import_entity
        iid = self.import_id
        import_id_v = new_doc[iid]
        if "individuals" in self.upstream:
            if not self.ind_coll.find_one({"id": ind_id}):
                self.log.append(f'individual {ind_id} for {ien} {import_id_v} should exist before {ien} import')
        if "biosamples" in self.upstream:
            if not self.bios_coll.find_one({"id": bios_id}):
                self.log.append(f'biosample {bios_id} for {ien} {import_id_v} should exist before {ien} import')
        if "analyses" in self.upstream:
            if not self.ana_coll.find_one({"id": ana_id}):
                self.log.append(f'analysis {ana_id} for {ien} {import_id_v} should exist before {ien} import')


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __parse_log(self):
        if len(self.log) < 1:
            return

        write_log(self.log, self.input_file)
        if (force := BYC_PARS.get("force")):
            print(f'¡¡¡ {len(self.log)} errors => still proceeding since"--force {force}" in effect')
        else:
            print(f'¡¡¡ {len(self.log)} errors => quitting w/o data changes\n... override with "--force true"')
            exit()

