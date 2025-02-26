import sys, re

from datetime import datetime
from os import path, environ
from pymongo import MongoClient

from bycon import (
    BYC,
    BYC_PARS,
    ByconFilters,
    ByconVariant,
    DB_MONGOHOST,
    ENV,
    prdbug,
    RefactoredValues,
    return_paginated_list,
    select_this_server,
    test_truthy
)

services_lib_path = path.join( path.dirname( path.abspath(__file__) ) )
sys.path.append( services_lib_path )
from interval_utils import GenomeBins
from datatable_utils import get_nested_value

################################################################################

class PGXfreq:
    def __init__(self, frequencysets=[]):
        self.frequencysets = frequencysets
        self.header_cols = ["reference_name", "start", "end", "gain_frequency", "loss_frequency", "no"]
        self.meta_items = ["group_id", "label", "dataset_id", "sample_count"]
        self.filename = "frequencies.pgxfreq"
        self.output_lines = []

        self.__add_meta_lines()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def stream_pgxfreq(self):
        self.__add_header_line()
        self.__add_frequency_lines()
        open_text_streaming(self.filename)
        for l in self.output_lines:
            print(l)
        exit()


    # -------------------------------------------------------------------------#

    def stream_pgxmatrix(self):
        self.filename = "interval_frequencies.pgxmatrix"
        self.__add_matrix_header_line()
        self.__add_frequency_matrix_lines()
        open_text_streaming(self.filename)
        for l in self.output_lines:
            print(l)
        exit()


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __add_meta_lines(self):
        g_b = GenomeBins().get_genome_binning()
        i_no = GenomeBins().get_genome_bin_count()
        self.output_lines.append(f'#meta=>genome_binning={g_b};interval_number={i_no}')
        for f_set in self.frequencysets:
            line = ["#group=>"]
            for k in self.meta_items:
                line.append(f'{k}={f_set.get(k, "___undefined___")}')
            self.output_lines.append(f'#group=>{";".join(line)}')


    # -------------------------------------------------------------------------#

    def __add_header_line(self):
        self.output_lines.append("\t".join(self.header_cols))


    # -------------------------------------------------------------------------#

    def __add_frequency_lines(self):
        for f_set in self.frequencysets:
            for intv in f_set.get("interval_frequencies", []):
                line = [f_set.get("group_id", "___undefined___")]
                for k in self.header_cols:
                    line.append(str(intv.get(k, "")))
                self.output_lines.append("\t".join(line))


    # -------------------------------------------------------------------------#

    def __add_matrix_header_line(self):
        g_b_s = GenomeBins().get_genome_bins()
        line = ["group_id"]
        for iv in g_b_s:
            line.append(f'{iv["reference_name"]}:{int(iv["start"]):09}-{int(iv["end"]):09}:DUP')
        for iv in g_b_s:
            line.append(f'{iv["reference_name"]}:{int(iv["start"]):09}-{int(iv["end"]):09}:DEL')
        self.output_lines.append("\t".join(line))


    # -------------------------------------------------------------------------#

    def __add_frequency_matrix_lines(self):
        for f_set in self.frequencysets:
            line = [f_set.get("group_id", "___undefined___")]
            for intv in f_set.get("interval_frequencies"):
                line.append( str(intv["gain_frequency"]) )
            for intv in f_set["interval_frequencies"]:
                line.append( str(intv["loss_frequency"]) )
            self.output_lines.append("\t".join(line))


################################################################################
################################################################################
################################################################################


class PGXseg:
    def __init__(self, dataset_results, ds_id=None):
        self.ds_id = ds_id if ds_id else list(dataset_results.keys())[0]
        self.skip = BYC_PARS.get("skip", 0)
        self.limit = BYC_PARS.get("limit", 0)
        self.datatable_mappings = BYC.get("datatable_mappings", {"$defs": {}})
        dataset_defs = BYC.get("dataset_definitions", {})
        self.dataset_definition = dataset_defs.get(self.ds_id, {})
        self.dataset_result = dataset_results.get(self.ds_id, {})
        self.mongo_client = MongoClient(host=DB_MONGOHOST)
        self.header_cols = self.datatable_mappings.get("ordered_pgxseg_columns", [])
        self.bios_pars = self.datatable_mappings["$defs"]["biosample"]["parameters"]
        self.var_pars = self.datatable_mappings["$defs"]["genomicVariant"]["parameters"]
        self.filename = "variants.pgxseg"
        self.output_lines = []

        self.__add_meta_lines()
        self.__add_header_line()
        self.__add_variants()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def stream_pgxseg(self):
        open_text_streaming(self.filename)
        for l in self.output_lines:
            print(l)
        return


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __add_meta_lines(self):
        if not (bios_ids := self.dataset_result.get("biosamples.id", {}).get("target_values")):
            BYC["ERRORS"].append("No biosamples found in the dataset results.")
            return
        bs_coll = self.mongo_client[self.ds_id]["biosamples"]
        for bs_id in bios_ids:
            if not (bs := bs_coll.find_one( {"id": bs_id})):
                continue
            line = self.__bios_meta_line(bs)
            self.output_lines.append(";".join(line))


    # -------------------------------------------------------------------------#

    def __bios_meta_line(self, bios):
        line = [f'#sample=>id={bios.get("id", "___undefined___")}']
        for par, par_defs in self.bios_pars.items():
            db_key = par_defs.get("db_key", "___undefined___")
            v = get_nested_value(bs, db_key)
            v = RefactoredValues(par_defs).strVal(v)
            if len(v) > 0:
                line.append(f'{par}={v}')
        return line


    # -------------------------------------------------------------------------#

    def __add_header_line(self):
        self.output_lines.append("\t".join(self.header_cols))


    # -------------------------------------------------------------------------#

    def __add_variants(self):
        if not (var_ids := self.dataset_result.get("variants.id", {}).get("target_values")):
            BYC["ERRORS"].append("No variants found in the dataset results.")
            return
        if test_truthy(BYC_PARS.get("paginate_results", True)):
            var_ids = return_paginated_list(var_ids, self.skip, self.limit)
        vs_coll = self.mongo_client[self.ds_id]["variants"]

        v_instances = []
        for v_id in var_ids:
            v_s = vs_coll.find_one({"id": v_id}, {"_id": 0})
            v_instances.append(ByconVariant().byconVariant(v_s))
        v_instances = list(sorted(v_instances, key=lambda x: (f'{x["location"]["chromosome"].replace("X", "XX").replace("Y", "YY").zfill(2)}', x["location"]['start'])))
        for v in v_instances:
            self.__variant_line(v)


    # -------------------------------------------------------------------------#

    def __variant_line(self, v_pgxseg):
        for p in ("sequence", "reference_sequence"):
            if not v_pgxseg[p]:
                v_pgxseg.update({p: "."})

        line = []
        for par in self.header_cols:
            par_defs = self.var_pars.get(par, {})
            db_key = par_defs.get("db_key", "___undefined___")
            v = get_nested_value(v_pgxseg, db_key)
            v = RefactoredValues(par_defs).strVal(v)
            line.append(v)
        self.output_lines.append("\t".join(line))


################################################################################
################################################################################
################################################################################

def __pgxmatrix_interval_header(info_columns):
    GBins = GenomeBins().get_genome_bins()
    int_line = info_columns.copy()
    for iv in GBins:
        int_line.append(f'{iv["reference_name"]}:{int(iv["start"]):09}-{int(iv["end"]):09}:DUP')
    for iv in GBins:
        int_line.append(f'{iv["reference_name"]}:{int(iv["start"]):09}-{int(iv["end"]):09}:DEL')
    return int_line


################################################################################

def print_filters_meta_line():
    if len(filters := ByconFilters().get_filters()) < 1:
        return
    f_vs = []
    for f in filters:
        f_vs.append(f.get("id", ""))
    print("#meta=>filters="+','.join(f_vs))


################################################################################

def write_variants_bedfile(datasets_results, ds_id):
    """
    ##### Accepts

    * a Bycon `h_o` handover object with its `target_values` representing `_id` 
    objects of a `variants` collection
        
    The function creates a basic BED file and returns its local path. A standard 
    use would be to create a link to this file and submit it as `hgt.customText` 
    parameter to the UCSC browser.

    ##### TODO

    * The creation of the different variant types is still rudimentary and has to be 
    expanded in lockstep with improving Beacon documentation and examples. The 
    definition of the types and their match patterns should also be moved to a 
    +separate configuration entry and subroutine.
    * evaluate to use "bedDetails" format

    """
    if not (local_paths := BYC.get("local_paths")):
        return False
    tmp_path = path.join( *local_paths[ "server_tmp_dir_loc" ])
    if not path.isdir(tmp_path):
        BYC["ERRORS"].append(f"Temporary directory `{tmp_path}` not found.")
        return False
    h_o_server = select_this_server()
    ext_url = f'http://genome.ucsc.edu/cgi-bin/hgTracks?org=human&db=hg38'
    bed_url = f'{h_o_server}/'

    vs = { "DUP": [ ], "DEL": [ ], "LOH": [ ], "SNV": [ ]}
    colors = {
        "plot_DUP_color": (255, 198, 51),
        "plot_AMP_color": (255,102,0),
        "plot_DEL_color": (51, 160, 255),
        "plot_HOMODEL_color": (0, 51, 204),
        "plot_LOH_color": (102, 170, 153),
        "plot_SNV_color": (255, 51, 204)
    }

    data_client = MongoClient(host=DB_MONGOHOST)
    v_coll = data_client[ ds_id ][ "variants" ]
    ds_results = datasets_results.get(ds_id, {})

    if not "variants.id" in ds_results:
        BYC["ERRORS"].append("No variants found in the dataset results.")
        return [ext_url, bed_url]

    v_ids = ds_results["variants.id"].get("target_values", [])
    v_count = ds_results["variants.id"].get("target_count", 0)
    accessid = ds_results["variants.id"].get("id", "___none___")
    if test_truthy( BYC_PARS.get("paginate_results", True) ):
        v_ids = return_paginated_list(v_ids, BYC_PARS.get("skip", 0), BYC_PARS.get("limit", 0))

    if len(v_ids) < 1:
        return [ext_url, bed_url]

    bed_file_name = f'{accessid}.bed'
    bed_file = path.join( tmp_path, bed_file_name )

    for v_id in v_ids:
        v = v_coll.find_one( { "id": v_id }, { "_id": 0 } )
        pv = ByconVariant().byconVariant(v)
        if (pvt := pv.get("variant_dupdel", "___none___")) not in vs.keys():
            continue
        pv.update({"variant_length": int(pv["location"].get("end", 1)) - int(pv["location"].get("start", 0))})
        vs[pvt].append(pv)

    b_f = open( bed_file, 'w' )
    pos = set()
    ucsc_chr = ""
    for vt in vs.keys():
        if len(vs[vt]) > 0:
            vs[vt] = sorted(vs[vt], key=lambda k: k['variant_length'], reverse=True)
            col_key = f"plot_{vt}_color"
            col_rgb = colors.get(col_key, (127, 127, 127))
            # col_rgb = [127, 127, 127]
            b_f.write(f'track name={vt} visibility=squish description=\"overall {v_count} variants matching the query; {len(vs[vt])} in this track\" color={col_rgb[0]},{col_rgb[1]},{col_rgb[2]}\n')
            b_f.write("#chrom\tchromStart\tchromEnd\tbiosampleId\n")
            for v in vs[vt]:
                ucsc_chr = "chr"+v["location"]["chromosome"]
                ucsc_min = int(v["location"]["start"]) + 1
                ucsc_max = int(v["location"]["end"] )
                l = f'{ucsc_chr}\t{ucsc_min}\t{ucsc_max}\t{v.get("biosample_id", "___none___")}\n'
                pos.add(ucsc_min)
                pos.add(ucsc_max)
                b_f.write( l )
 
    b_f.close()
    ucsc_range = sorted(pos)
    ucsc_pos = "{}:{}-{}".format(ucsc_chr, ucsc_range[0], ucsc_range[-1])
    ext_url = f'{ext_url}&position={ucsc_pos}&hgt.customText='
    bed_url = f'{h_o_server}{local_paths.get("server_tmp_dir_web", "/tmp")}/{bed_file_name}'

    return [ext_url, bed_url]


################################################################################

def export_callsets_matrix(datasets_results, ds_id):
    skip = BYC_PARS.get("skip", 0)
    limit = BYC_PARS.get("limit", 0)
    g_b = BYC_PARS.get("genome_binning", "")
    i_no = GenomeBins().get_genome_bin_count()

    m_format = "values" if "val" in BYC_PARS.get("output", "") else "coverage"

    if not (cs_r := datasets_results[ds_id].get("analyses.id")):
        return
    mongo_client = MongoClient(host=DB_MONGOHOST)
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]
    cs_coll = mongo_client[ ds_id ][ "analyses" ]

    open_text_streaming("interval_callset_matrix.pgxmatrix")

    for d in ["id", "assemblyId"]:
        if (d_v := BYC["dataset_definitions"][ds_id].get(d)):
            print(f'#meta=>{d}={d_v}')
    print_filters_meta_line()
    print(f'#meta=>data_format=interval_{m_format}')

    info_columns = [ "analysis_id", "biosample_id", "group_id" ]
    h_line = __pgxmatrix_interval_header(info_columns)
    info_col_no = len(info_columns)
    int_col_no = len(h_line) - len(info_columns)
    print(f'#meta=>genome_binning={g_b};interval_number={i_no}')
    print(f'#meta=>no_info_columns={info_col_no};no_interval_columns={int_col_no}')

    q_vals = cs_r["target_values"]
    r_no = len(q_vals)
    if r_no > limit:
        if test_truthy( BYC_PARS.get("paginate_results", True) ):
            q_vals = return_paginated_list(q_vals, skip, limit)
        print(f'#meta=>"WARNING: Only {len(q_vals)} analyses will be included due to pagination skip {skip} and limit {limit}."')

    bios_ids = set()
    cs_ids = {}
    cs_cursor = cs_coll.find({"id": {"$in": q_vals }, "cnv_statusmaps": {"$exists": True}} )
    for cs in cs_cursor:
        bios = bs_coll.find_one( { "id": cs["biosample_id"] } )
        bios_ids.add(bios["id"])
        s_line = "#sample=>biosample_id={};analysis_id={}".format(bios["id"], cs["id"])
        h_d = bios["histological_diagnosis"]
        cs_ids.update({cs["id"]: h_d.get("id", "NA")})
        print(f'{s_line};group_id={h_d.get("id", "NA")};group_label={h_d.get("label", "NA")};NCIT::id={h_d.get("id", "NA")};NCIT::label={h_d.get("label", "NA")}')

    print("#meta=>biosampleCount={};analysisCount={}".format(len(bios_ids), cs_r["target_count"]))
    print("\t".join(h_line))

    for cs_id, group_id in cs_ids.items():
        cs = cs_coll.find_one({"id":cs_id})
        if "values" in m_format:
            print("\t".join(
                [
                    cs_id,
                    cs.get("biosample_id", "NA"),
                    group_id,
                    *map(str, cs["cnv_statusmaps"]["max"]),
                    *map(str, cs["cnv_statusmaps"]["min"])
                ]
            ))
        else:
            print("\t".join(
                [
                    cs_id,
                    cs.get("biosample_id", "NA"),
                    group_id,
                    *map(str, cs["cnv_statusmaps"]["dup"]),
                    *map(str, cs["cnv_statusmaps"]["del"])
                ]
            ))

    close_text_streaming()


################################################################################

def export_vcf_download(datasets_results, ds_id):
    """
    """
    # TODO: VCF schema in some config file...
    skip = BYC_PARS.get("skip", 0)
    limit = BYC_PARS.get("limit", 0)
    open_text_streaming(f"{ds_id}_variants.vcf")
    print(
        """##fileformat=VCFv4.4
##reference=GRCh38
##ALT=<ID=DUP,Description="Duplication">
##ALT=<ID=DEL,Description="Deletion">
##INFO=<ID=END,Number=1,Type=Integer,Description="End position of the longest variant described in this record">
##INFO=<ID=SVLEN,Number=A,Type=Integer,Description="Length of structural variant">
##INFO=<ID=CN,Number=A,Type=Float,Description="Copy number of CNV/breakpoint">
##INFO=<ID=SVCLAIM,Number=A,Type=String,Description="Claim made by the structural variant call. Valid values are D, J, DJ for abundance, adjacency and both respectively">
##INFO=<ID=IMPRECISE,Number=0,Type=Flag,Description="Imprecise structural variation">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">"""
    )

    v_o = {
        "#CHROM": ".",
        "POS": ".",
        "ID": ".",
        "REF": ".",
        "ALT": ".",
        "QUAL": ".",
        "FILTER": "PASS",
        "FORMAT": "",
        "INFO": ""
    }

    data_client = MongoClient(host=DB_MONGOHOST)
    v_coll = data_client[ ds_id ][ "variants" ]
    ds_results = datasets_results.get(ds_id, {})
    if not "variants.id" in ds_results:
        BYC["ERRORS"].append("No variants found in the dataset results.")
        return
    v_ids = ds_results["variants.id"].get("target_values", [])
    if test_truthy( BYC_PARS.get("paginate_results", True) ):
        v_ids = return_paginated_list(v_ids, skip, limit)

    v_instances = []
    for v_id in v_ids:
        v = v_coll.find_one( { "id": v_id }, { "_id": 0 } )
        v_instances.append(ByconVariant().byconVariant(v))


    v_instances = list(sorted(v_instances, key=lambda x: (f'{x["location"]["chromosome"].replace("X", "XX").replace("Y", "YY").zfill(2)}', x["location"]['start'])))

    variant_ids = []
    for v in v_instances:
        v_iid = v.get("variant_internal_id", "__none__")
        if v_iid not in variant_ids:
            variant_ids.append(v_iid)

    biosample_ids = []
    for v in v_instances:
        biosample_ids.append(v.get("biosample_id", "__none__"))
    # no duplicates here since each has its column
    biosample_ids = list(set(biosample_ids))

    for bsid in biosample_ids:
        v_o.update({bsid: "."})

    print("\t".join(v_o.keys()))

    bv = ByconVariant()
    for d in variant_ids:
        d_vs = [var for var in v_instances if var.get('variant_internal_id', "__none__") == d]
        vcf_v = bv.vcfVariant(d_vs[0])
        for bsid in biosample_ids:
            vcf_v.update({bsid: "."})
        for d_v in d_vs:
            b_i = d_v.get("biosample_id", "__none__")
            vcf_v.update({b_i: "0/1"})

        r_l = map(str, list(vcf_v.values()))
        print("\t".join(r_l))
        
    close_text_streaming()


################################################################################

def open_text_streaming(filename="data.pgxseg"):
    if not "___shell___" in ENV:
        print('Content-Type: text/plain')
        print(f'Content-Disposition: attachment; filename="{filename}"')
        print('status: 200')
        print()


################################################################################

def close_text_streaming():
    print()
    prdbug(f'... closing text streaming at {datetime.now().strftime("%H:%M:%S")}')
    exit()
