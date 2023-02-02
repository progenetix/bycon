import csv, datetime, re, time, base36
from os import path, pardir

# local
from variant_parsing import variant_create_digest

bycon_lib_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( bycon_lib_path, pardir )

################################################################################
################################################################################
################################################################################

def parse_cytoband_file(byc):

    """podmd
 
    podmd"""
    # TODO: catch error for missing genome edition
    g_map = byc["interval_definitions"]["genome_path_ids"].get("values", {})

    genome = byc["variant_pars"][ "assembly_id" ].lower()
    genome = re.sub( r"(\w+?)([^\w]\w+?)", r"\1", genome)

    if genome in g_map.keys():
        genome = g_map[ genome ]

    cb_file = path.join( pkg_path, "rsrc", "genomes", genome, "cytoBandIdeo.txt" )   
    cb_re = re.compile( byc["interval_definitions"][ "cytobands" ][ "pattern" ] )
    cb_keys = [ "chro", "start", "end", "cytoband", "staining" ]

    cytobands = [ ]
    cytolimits = { }
    genome_size = 0

    i = 0

    c_bands = [ ]
    with open(cb_file) as cb_f:                                                                                          
        for c_band in csv.DictReader(filter(lambda row: row[0]!='#', cb_f), fieldnames=cb_keys, delimiter='\t'):
            c_bands.append(c_band)

    # !!! making sure the chromosomes are sorted !!!
    for chro in byc["interval_definitions"][ "chromosomes" ]:
        c_m = "chr"+str(chro)
        chrobands = [ ]
        for cb in c_bands:
            if cb[ "chro" ] == c_m:
                cb[ "i" ] = i
                cb[ "chro" ] = cb[ "chro" ].replace( "chr", "")
                cb[ "chroband" ] = cb[ "chro" ]+cb[ "cytoband" ]
                cytobands.append(dict(cb))
                chrobands.append(dict(cb))
                i += 1
        cytolimits.update({
            chro: {
                "chro": [ int(cytobands[0]["start"]), int(cytobands[-1]["end"]) ],
                "size": int(cytobands[-1]["end"]) - int(cytobands[0]["start"]),
                "p": arm_base_range(chro, "p", cytobands),
                "q": arm_base_range(chro, "q", cytobands)
            }
        })
        genome_size += int(chrobands[-1]["end"])

    
    byc.update( {
        "cytobands": cytobands,
        "cytolimits": cytolimits,
        "genome_size": genome_size
    } )

    return byc

################################################################################

def bands_from_cytobands(chr_bands, byc):

    cb_pat = re.compile( byc["variant_definitions"]["parameters"]["cyto_bands"]["pattern"] )
    error = ""

    end_re = re.compile(r"^([pq]\d.*?)\.?\d$")
    arm_re = re.compile(r"^([pq]).*?$")
    p_re = re.compile(r"^p.*?$")
    q_re = re.compile(r"^q.*?$")

    # chr_bands = "4pcenqcen"

    if "p10" in chr_bands:
        chr_bands = re.sub("p10", "pcen", chr_bands)
    if "q10" in chr_bands:
        chr_bands = re.sub("q10", "qcen", chr_bands)

    # print("|||-"+chr_bands+"-|||")

    chro, cb_start, cb_end = cb_pat.match(chr_bands).group(1,2,3)

    cytobands = list(filter(lambda d: d[ "chro" ] == chro, byc["cytobands"].copy()))
    if len(cytobands) < 10:
        return([], "", "", "", "error")

    if cb_start is None and cb_end is None:
        return cytobands, chro, int( cytobands[0]["start"] ), int( cytobands[-1]["end"] ), error

    p_bands = list(filter(lambda d: p_re.match(d[ "cytoband" ]), cytobands))
    q_bands = list(filter(lambda d: q_re.match(d[ "cytoband" ]), cytobands))

    # if there was no end, the start band is queried again until its last match
    if cb_end is None:
        cb_end = cb_start

    if "qter" in cb_start:
        cb_start = cytobands[-1]["cytoband"]
    if "qter" in cb_end:
        cb_end = cytobands[-1]["cytoband"]
    if "pter" in cb_start:
        cb_start = cytobands[0]["cytoband"]
    if "pter" in cb_end:
        cb_end = cytobands[0]["cytoband"]
    if "pcen" in cb_start:
        cb_start = p_bands[-1]["cytoband"]
    if "pcen" in cb_end:
        cb_end = p_bands[-1]["cytoband"]
    if "qcen" in cb_start:
        cb_start = q_bands[0]["cytoband"]
    if "qcen" in cb_end:
        cb_end = q_bands[0]["cytoband"]

    if "p" in cb_end:
        if "q" in cb_start:
            cb_start, cb_end = cb_end, cb_start

    # using a numeric comparison to sort bands for p higher to lower
    cb_re = re.compile(r'^([pq])((\d)(?:\d(?:\.\d\d?\d?)?)?)$', re.IGNORECASE)
    if cb_re.match(cb_start) and cb_re.match(cb_end):
        fb1 = float( cb_re.match(cb_start).group(2) )
        fb2 = float( cb_re.match(cb_end).group(2) )
        arm1 = cb_re.match(cb_start).group(1)
        arm2 = cb_re.match(cb_end).group(1)
        mb1 = int( cb_re.match(cb_start).group(3) )
        mb2 = int( cb_re.match(cb_end).group(3) )
        if arm1 == arm2:
            if "p" in arm1:
                if not mb1 > mb2:
                    if fb2 > fb1:
                        cb_start, cb_end = cb_end, cb_start
            elif "q" in arm1:
                if not mb2 > mb1:
                    if fb2 < fb1:
                        cb_start, cb_end = cb_end, cb_start

    # print("\n", chro, cb_start, cb_end, chr_bands)

    # TODO: this is ugly - someho whad problems w/ recursion version :-/
    start_bands = match_bands(cb_start, cytobands)
    if len(start_bands) < 1:
        if end_re.match(cb_start):
            band = end_re.match(cb_start).group(1)
            start_bands = match_bands(band, cytobands)
            if len(start_bands) < 1:
                if arm_re.match(cb_start):
                    band = arm_re.match(cb_start).group(1)
                    start_bands = match_bands(band, cytobands)

    end_bands = match_bands(cb_end, cytobands)
    if len(end_bands) < 1:
        if end_re.match(cb_end):
            band = end_re.match(cb_end).group(1)
            end_bands = match_bands(band, cytobands)
            if len(end_bands) < 1:
                if arm_re.match(cb_end):
                    band = arm_re.match(cb_end).group(1)
                    end_bands = match_bands(band, cytobands)

    cb_from = start_bands[0]["i"]
    cb_to = end_bands[-1]["i"] + 1

    matched = byc["cytobands"][cb_from:cb_to]
 
    return matched, chro, int( matched[0]["start"] ), int( matched[-1]["end"]), error

################################################################################

def match_bands(band, cytobands):

    cb_re = re.compile(rf"^{band}", re.IGNORECASE)
    m_b_s = list( filter(lambda d:cb_re.match(d["cytoband"]), cytobands) )
    return m_b_s

################################################################################

def arm_base_range(chro, arm, cytobands):

    if arm not in ["p","q", "P", "Q"]:
        return 0, 1

    arm_re = re.compile(rf"^{arm}", re.IGNORECASE)
    bands = list(filter(lambda d: d[ "chro" ] == chro, cytobands))
    bands = list(filter(lambda d: arm_re.match(d[ "cytoband" ]), bands))

    return [ int(bands[0]["start"]), int(bands[-1]["end"]) ]

################################################################################

def cytobands_label( cytobands ):

    cb_label = ""

    if len(cytobands) > 0:

        # cb_label = cytobands[0]["chro"]+cytobands[0]["cytoband"]
        cb_label = cytobands[0]["cytoband"]
        if len( cytobands ) > 1:
            cb_label = cb_label+cytobands[-1]["cytoband"]

    return cb_label

################################################################################

def translate_reference_ids(byc):

    if not "variant_definitions" in byc:
        return byc

    v_d_refsc = byc["variant_definitions"]["refseq_chromosomes"]
    c_r = {}
    r_c = {}
    r_a = {}
    c_a = {}
    for c, c_d in v_d_refsc.items():
        refseq_stripped = re.sub("refseq:", "", c_d["refseq_id"])
        c_r.update({ c_d["chr"]: c_d["refseq_id"] })
        r_c.update({ c_d["refseq_id"]: c_d["chr"] })
        r_a.update({
            c: c_d["refseq_id"],
            c_d["chr"]: c_d["refseq_id"],
            c_d["refseq_id"]: c_d["refseq_id"],
            refseq_stripped: c_d["refseq_id"],
            c_d["genbank_id"]: c_d["refseq_id"]
        }),
        c_a.update({
            c: c_d["chr"],
            c_d["chr"]: c_d["chr"],
            c_d["refseq_id"]: c_d["chr"],
            refseq_stripped: c_d["chr"],
            c_d["genbank_id"]: c_d["chr"]
        })
    byc["variant_definitions"].update({
        "chro_refseq_ids": c_r,
        "refseq_chronames": r_c,
        "refseq_aliases": r_a,
        "chro_aliases": c_a
    })

    return byc

################################################################################

def variants_from_revish(bs_id, cs_id, technique, iscn, byc):

    v_s, v_e = deparse_ISCN_to_variants(iscn, byc)
    variants = []

    for v in v_s:

        v.update({
            "id": generate_id("pgxvar"),
            "variant_internal_id": variant_create_digest(v, byc),
            "biosample_id": bs_id,
            "callset_id": cs_id,
            "updated": datetime.datetime.now().isoformat()
        })

        variants.append(v)

    return variants, v_e

################################################################################

def deparse_ISCN_to_variants(iscn, byc):

    iscn = "".join(iscn.split())
    variants = []
    vd = byc["variant_definitions"]
    cb_pat = re.compile( vd["parameters"]["cyto_bands"]["pattern"] )
    errors = []

    for cnv_t, cnv_defs in vd["cnv_iscn_defs"].items():

        revish = cnv_defs["info"]["revish_label"]

        iscn_re = re.compile(rf"^.*?{revish}\(([\w.,]+)\).*?$", re.IGNORECASE)

        if iscn_re.match(iscn):

            m = iscn_re.match(iscn).group(1)

            for i_v in re.split(",", m):

                if not cb_pat.match(i_v):
                    continue

                cytoBands, chro, start, end, error = bands_from_cytobands(i_v, byc)
                if len(error) > 0:
                    errors.append(error)
                    continue

                v_l = end - start
                t = cnv_t
                v = cnv_defs.copy()

                cytostring = "{}({})".format(cnv_t, i_v).lower()

                if "AMP" in cnv_t and v_l > vd["amp_max_size"]:
                    t = "HLDUP"
                    v = vd["cnv_iscn_defs"][t].copy()

                v_s = {}
               
                v.update({
                    "type": "RelativeCopyNumber",
                    "location": {
                        "sequence_id": vd["refseq_aliases"][chro],
                        "type": 'SequenceLocation',
                        "interval": {
                            "start": {
                                "type": 'Number',
                                "value": start
                            },
                            "end": {
                                "type": 'Number',
                                "value": end
                            }
                        }
                    },
                    "info": {
                        "ISCN": cytostring,
                        "var_length": v_l,
                        "cnv_value": vd["cnv_dummy_values"][t]
                    }
                })

                variants.append(v)

    return variants, " :: ".join(errors)

################################################################################

def cytobands_label_from_positions(byc, chro, start, end):

    cytobands, chro, start, end = cytobands_list_from_positions(byc, chro, start, end)
    cbl = cytobands_label( cytobands )

    return cbl

################################################################################

def bands_from_chrobases(chro_bases, byc):

    cb_pat = re.compile( byc["variant_definitions"]["parameters"]["chro_bases"]["pattern"] )
    chro, cb_start, cb_end = cb_pat.match(chro_bases).group(2,3,5)

    return cytobands_list_from_positions(byc, chro, cb_start, cb_end)

################################################################################

def cytobands_list_from_positions(byc, chro, start=None, end=None):

    if start:
        start = int(start)
        if not end:
            end = start + 1
        end = int(end)

    cytobands = list(filter(lambda d: d[ "chro" ] == chro, byc["cytobands"]))
    if start == None:
        start = 0
    if end == None:
        end = int( cytoBands[-1]["end"] )

    if isinstance(start, int):
        cytobands = list(filter(lambda d: int(d[ "end" ]) > start, cytobands))

    if isinstance(end, int):
        cytobands = list(filter(lambda d: int(d[ "start" ]) < end, cytobands))
    else:
        print(end)

    return cytobands, chro, start, end

################################################################################

def generate_id(prefix):

    time.sleep(.001)
    return '{}-{}'.format(prefix, base36.dumps(int(time.time() * 1000))) ## for time in ms

