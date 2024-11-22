import csv, re
from os import path

from bycon_helpers import prdbug
from config import *
from genome_utils import ChroNames

################################################################################
################################################################################
################################################################################

class Cytobands():
    """
    The `Cytobands()` class provides methods to access cytoband information from
    a standard UCSC-style cytoband file (cytoBandIdeo.txt), to filter those for
    cytoband or genomic ranges and to convert between cytoband and genomic coordinates.
    """

    def __init__(self):
        self.cytobands = [ ]
        self.cytolimits = { }
        self.genome_size = 0
        self.filtered_bands = []
        self.chro = None
        self.start = None
        self.end = None
        self.ChroNames = ChroNames()
        self.cytoband_response = {}
        self.sorted_chros = BYC["interval_definitions"]["chromosomes"]

        self.__parse_cytoband_file()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_all_cytobands(self):
        return self.cytobands


    # -------------------------------------------------------------------------#

    def get_all_cytolimits(self):
        return self.cytolimits


    # -------------------------------------------------------------------------#

    def get_genome_size(self):
        return self.genome_size


    # -------------------------------------------------------------------------#

    def cytobands_response(self):
        self.__cytobands_from_request_pars()
        self.__cytobands_response_object()
        return self.cytoband_response


    # -------------------------------------------------------------------------#

    def bands_from_cytostring(self, cytoband=""):
        self.cytostring = cytoband
        self.__bands_from_cytobands()
        return self.filtered_bands, self.chro, self.start, self.end


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __cytobands_from_request_pars(self):
        if (c_b := BYC_PARS.get("cyto_bands")):
            self.cytostring = c_b
            self.__bands_from_cytobands()
        if (c_b := BYC_PARS.get("chro_bases", [])):
            self.filtered_bands, self.chro, self.start, self.end = bands_from_chrobases(c_b)
        else:
            return

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __cytobands_response_object(self):
        if len(self.filtered_bands) < 1:
            BYC["ERRORS"].append("No matching cytobands!")
            return

        cb_label = cytobands_label(self.filtered_bands)
        size = int(self.end - self.start)
        chro_bases = f'{self.chro}:{self.start}-{self.end}'
        sequence_id = self.ChroNames.refseq(self.chro)

        self.cytoband_response = {
            "info": {
                "cytoBands": cb_label,
                "bandList": [x['chroband'] for x in self.filtered_bands ],
                "chroBases": chro_bases,
                "referenceName": self.chro,
                "size": size,
            },        
            "chromosome_location": {
                "type": "ChromosomeLocation",
                "species_id": "taxonomy:9606",
                "chr": self.chro,
                "interval": {
                    "start": self.filtered_bands[0]["cytoband"],
                    "end": self.filtered_bands[-1]["cytoband"],
                    "type": "CytobandInterval"
                }
            },
            "genomic_location": {
                "type": "SequenceLocation",
                "sequence_id": sequence_id,
                "interval": {
                    "start": {
                        "type": "Number",
                        "value": self.start
                    },
                    "end": {
                        "type": "Number",
                        "value": self.end
                    },
                    "type": "SequenceInterval"
                }
            }
        }


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __parse_cytoband_file(self):
        g_rsrc_p = self.ChroNames.genomePath()
        cb_file = path.join(g_rsrc_p, "cytoBandIdeo.txt")
        cb_keys = [ "chro", "start", "end", "cytoband", "staining" ]
        i = 0
        c_bands = [ ]
        with open(cb_file) as cb_f:                                                                                          
            for c_band in csv.DictReader(filter(lambda row: row.startswith('#') is False, cb_f), fieldnames=cb_keys, delimiter='\t'):
                c_bands.append(c_band)

        #--------------------------------------------------------------------------#

        # !!! making sure the chromosomes are sorted !!!
        # TODO: should be in ChroNames?
        for chro in self.sorted_chros:
            chro = str(chro)
            c_m = f'chr{chro}'
            chrobands = [ ]
            for cb in c_bands:
                if cb["chro"] == c_m:
                    cb["i"] = i
                    cb["chro"] = cb["chro"].replace("chr", "")
                    cb["chroband"] = f'{cb["chro"]}{cb["cytoband"]}'
                    self.cytobands.append(dict(cb))
                    chrobands.append(dict(cb))
                    i += 1
            self.cytolimits.update({
                chro: {
                    "chro": [ int(chrobands[0]["start"]), int(chrobands[-1]["end"]) ],
                    "size": int(chrobands[-1]["end"]) - int(chrobands[0]["start"]),
                    "p": arm_base_range("p", chrobands),
                    "q": arm_base_range("q", chrobands)
                }
            })
            self.genome_size += int(chrobands[-1]["end"])

    #--------------------------------------------------------------------------#

    def __bands_from_cytobands(self):
        argdefs = BYC["argument_definitions"].get("$defs", {})
        cb_pat = re.compile( argdefs["cyto_bands"]["pattern"] )
        end_re = re.compile(r"^([pq]\d.*?)\.?\d$")
        arm_re = re.compile(r"^([pq]).*?$")
        p_re = re.compile(r"^p.*?$")
        q_re = re.compile(r"^q.*?$")

        chr_bands = self.cytostring

        if "p10" in chr_bands:
            chr_bands = re.sub("p10", "pcen", chr_bands)
        if "q10" in chr_bands:
            chr_bands = re.sub("q10", "qcen", chr_bands)

        if not cb_pat.match(chr_bands):
            return([], "", "", "")

        chro, cb_start, cb_end = cb_pat.match(chr_bands).group(1,2,3)
        cytobands = list(filter(lambda d: d["chro"] == chro, self.cytobands.copy()))

        if len(cytobands) < 10:
            BYC["ERRORS"].append(f"No matching cytobands for chromosome {chro}!")
            return

        if cb_start is None and cb_end is None:
            self.filtered_bands = cytobands
            self.chro = chro
            self.start = int( cytobands[0]["start"] )
            self.end = int( cytobands[-1]["end"])
            return

        p_bands = list(filter(lambda d: p_re.match(d["cytoband"]), cytobands))
        q_bands = list(filter(lambda d: q_re.match(d["cytoband"]), cytobands))

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

        # TODO: this is ugly - somehow had problems w/ recursion version :-/
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

        matched = self.cytobands[cb_from:cb_to]

        self.filtered_bands = matched
        self.chro = chro
        self.start = int( matched[0]["start"] )
        self.end = int( matched[-1]["end"])

    #--------------------------------------------------------------------------#



################################################################################

def match_bands(band, cytobands):
    cb_re = re.compile(rf"^{band}", re.IGNORECASE)
    m_b_s = list( filter(lambda d:cb_re.match(d["cytoband"]), cytobands) )
    return m_b_s


################################################################################

def arm_base_range(arm, chrobands):
    if arm not in ["p","q", "P", "Q"]:
        return 0, 1
    arm_re = re.compile(rf"^{arm}", re.IGNORECASE)
    bands = list(filter(lambda d: arm_re.match(d[ "cytoband" ]), chrobands))
    return [ int(bands[0]["start"]), int(bands[-1]["end"]) ]


################################################################################

def cytobands_label(cytobands):
    """
    Receives: (potentially filtered) list of cytoband objects
    Returns: the concatenated first and last cytoband label
    Examples:
      - p12.2q22.2
      - q13.1
    """

    cb_label = ""

    if len(cytobands) > 0:
        cb_label = cytobands[0].get("cytoband", "")
        if len( cytobands ) > 1:
            cb_label = cb_label+cytobands[-1].get("cytoband", "")

    return cb_label


################################################################################

def cytobands_label_from_positions(chro, start, end):
    cytobands, chro, start, end = cytobands_list_from_positions(chro, start, end)
    cbl = cytobands_label(cytobands)
    return cbl


################################################################################

def bands_from_chrobases(chro_bases):
    argdefs = BYC["argument_definitions"].get("$defs", {})
    cb_pat = re.compile( argdefs["chro_bases"]["pattern"] )
    if not cb_pat.match(chro_bases):
        return [], "NA", 0, 0
    chro, cb_start, cb_end = cb_pat.match(chro_bases).group(2,3,5)
    return cytobands_list_from_positions(chro, cb_start, cb_end)


################################################################################

def cytobands_list_from_positions(chro, start=None, end=None):
    cytobands = Cytobands().get_all_cytobands()
    if start:
        start = int(start)
        if not end:
            end = start + 1
        end = int(end)

    cytobands = list(filter(lambda d: d[ "chro" ] == chro, cytobands))
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

