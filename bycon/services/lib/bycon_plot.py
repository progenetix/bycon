import base64, inspect, io, re, sys
from datetime import datetime, date
from humps import decamelize
from os import environ, path
from PIL import Image, ImageColor, ImageDraw

from bycon import BYC, BYC_PARS, ENV, bands_from_cytobands, prjsonnice, test_truthy, prdbug, GeneInfo, ChroNames

services_lib_path = path.join( path.dirname( path.abspath(__file__) ) )
sys.path.append( services_lib_path )
from clustering_utils import cluster_frequencies, cluster_samples

# http://progenetix.org/services/sampleplots?&filters=pgx:icdom-85003&plotType=histoplot&skip=0&limit=100&plotPars=plot_chros=8,9,17::labels=8:120000000-123000000:Some+Interesting+Region::plot_gene_symbols=MYCN,REL,TP53,MTAP,CDKN2A,MYC,ERBB2,CDK1::plot_width=800&filters=pgx:icdom-85003&plotType=histoplot
# http://progenetix.org/services/samplesplot?datasetIds=progenetix&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&plotType=histoplot&plotPars=plot_gene_symbols=CDKN2A,MTAP,EGFR,BCL6
# http://progenetix.org/services/samplesplot?datasetIds=progenetix&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&plotType=samplesplot&plotPars=plot_gene_symbols=CDKN2A,MTAP,EGFR,BCL6

################################################################################
################################################################################
################################################################################

class ByconPlotPars:

    def __init__(self):

        self.plot_type = BYC_PARS.get("plot_type", "histoplot")
        self.plot_defaults = BYC.get("plot_defaults", {})
        p_t_s = self.plot_defaults.get("plot_type_defs", {})
        p_d_p = self.plot_defaults.get("plot_parameters", {})

        self.plv = {}

        p_t = self.plot_type
        if not (p_t_d := p_t_s.get(p_t)):
            self.plot_type = "histoplot"
            p_t_d = p_t_s.get("histoplot")

        p_d_m = p_t_d.get("mods", {})

        for p_k, p_d in p_d_p.items():
            if "default" in p_d:
                self.plv.update({p_k: p_d["default"]})
                if (p_k := p_d_m):
                    self.plv.update({p_k: p_d_m[p_k]})
            else:
                self.plv.update({p_k: ""})

        m_t = p_t_d.get("modded")
        if m_t:
            self.plot_type = m_t


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def plotType(self):
        return self.plot_type


    # -------------------------------------------------------------------------#

    def plotTypeDefinitions(self):
        return self.plot_defaults.get("plot_type_defs", {})


    # -------------------------------------------------------------------------#

    def plotDefaults(self):
        return self.plv


    # -------------------------------------------------------------------------#

    def plotParameters(self, modded={}):
        for m_k, m_v in modded.items():
            self.plv.update({m_k: m_v})
        self.__process_plot_parameters()
        return self.plv


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __process_plot_parameters(self):
        p_d_p = self.plot_defaults.get("plot_parameters", {})

        bps = {}
        plot_pars = BYC_PARS.get("plot_pars", "")
        prdbug(f'__process_plot_parameters - all: {plot_pars}')
        for ppv in re.split(r'::|&', plot_pars):
            pp_pv = ppv.split('=')
            if len(pp_pv) == 2:
                pp, pv = pp_pv
                if pv in ["null", "undefined"]:
                    continue
                pp = decamelize(pp)
                bps.update({pp: pv})
                prdbug(f'__process_plot_parameters {pp} => {pv}')

        dbm = f'... plotPars: {bps}'
        for p_k, p_d in p_d_p.items():
            if p_k in bps:
                p_k_t = p_d_p[p_k].get("type", "string")
                p_d = bps.get(p_k)
                dbm = f'{p_k}: {p_d} ({p_k_t}), type {type(p_d)}'
                if "array" in p_k_t:
                    p_i_t = p_d_p[p_k].get("items", "string")
                    prdbug(f'... plot parameter {p_k}: {p_d}')
                    if type(p_d) is not list:
                        p_d = re.split(',', p_d)
                    if "int" in p_i_t:
                        p_d = list(map(int, p_d))
                    elif "number" in p_i_t:
                        p_d = list(map(float, p_d))
                    else:
                        p_d = list(map(str, p_d))

                    if len(p_d) > 0:
                        self.plv.update({p_k: p_d})
                elif "int" in p_k_t:
                    self.plv.update({p_k: int(p_d)})
                elif "num" in p_k_t:
                    self.plv.update({p_k: float(p_d)})
                elif "bool" in p_k_t:
                    self.plv.update({p_k: p_d})
                else:
                    self.plv.update({p_k: str(p_d)})

        # # TODO: map potential NC_ values
        # k = "plot_chros"
        # p_cs = bps.get(k, [])
        # if len(p_cs) > 0:
        #     self.plv.update({k: [ChroNames().chro(x) for x in p_cs]})


################################################################################
################################################################################
################################################################################

class ByconPlot:
    """
    # The `ByconPlot` class

    ## Input

    A plot data bundle containing lists of callset object bundles (_i.e._ the
    analyses with all their individual variants added) and/or interval frequencies
    set bundles (_i.e._ list of one or more binned CNV frequencies in object
    wrappers with some information about the set).
 
    """

    def __init__(self, plot_data_bundle: dict):
        bpp = ByconPlotPars()
        self.plot_type = bpp.plotType()
        prdbug(f"... plot_type: {self.plot_type}")
        self.plot_type_defs = bpp.plotTypeDefinitions()
        self.plv = bpp.plotDefaults()

        self.cytobands = BYC.get("cytobands", [])
        self.cytolimits = BYC.get("cytolimits", {})
        self.plot_data_bundle = plot_data_bundle
        self.svg = None
        self.plot_time_init = datetime.now()

        self.__plot_pipeline()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_svg(self) -> str:
        return self.svg


    # -------------------------------------------------------------------------#

    def svg2file(self, filename):
        svg_fh = open(filename, "w")
        svg_fh.write(self.svg)
        svg_fh.close()


    # -------------------------------------------------------------------------#

    def svgResponse(self):
        self.__print_svg_response()


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_pipeline(self):
        dbm = f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}'
        prdbug(dbm)
        self.plot_pipeline_start = datetime.now()
        self.__initialize_plot_values()
        if self.__plot_respond_empty_results() is False:
            self.__plot_add_title()
            self.__plot_add_cytobands()
            self.__plot_add_samplestrips()
            self.__plot_add_histodata()
            self.__plot_add_probesplot()
            self.__plot_add_cluster_tree()
            self.__plot_add_markers()
        self.__plot_add_footer()

        self.svg = self.__create_svg()
        self.plot_pipeline_end = datetime.now()
        self.plot_pipeline_duration = self.plot_pipeline_end - self.plot_pipeline_start
        dbm = f'... plot pipeline duration for {self.plot_type} was {self.plot_pipeline_duration.total_seconds()} seconds'
        prdbug(dbm)


    # -------------------------------------------------------------------------#

    def __initialize_plot_values(self):
        dbm = f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}'
        prdbug(dbm)

        p_t_s = self.plot_type_defs
        p_t = self.plot_type
        d_k = p_t_s[p_t].get("data_key")
        d_t = p_t_s[p_t].get("data_type", "analyses")

        sample_count = 0

        # TODO: get rid of the "results"?
        self.plv.update({
            "results": self.plot_data_bundle.get(d_k, []),
            "results_number": len(self.plot_data_bundle.get(d_k, [])),
            "data_type": d_t,
        })
        self.plv.update({
            "dataset_ids": list(set([s.get("dataset_id", "NA") for s in self.plv["results"]]))
        })

        self.__filter_empty_callsets_results()

        if self.plv["results_number"] < 2:
            self.plv.update({"plot_labelcol_width": 0})

        if self.plv["results_number"] > 2:
            self.plv.update({"plot_cluster_results": True})
        else:
            self.plv.update({"plot_dendrogram_width": 0})

        self.plv.update(ByconPlotPars().plotParameters(self.plv))

        prdbug(f'... testing plot_width: {self.plv["plot_width"]}')

        pax = self.plv["plot_margins"] + self.plv["plot_labelcol_width"] + self.plv["plot_axislab_y_width"]
        paw = self.plv["plot_width"] - 2 * self.plv["plot_margins"]
        paw -= self.plv["plot_labelcol_width"]
        paw -= self.plv["plot_axislab_y_width"]
        paw -= self.plv["plot_dendrogram_width"]

        # calculate the base
        chr_b_s = 0
        
        c_l_s = dict(self.cytolimits)
        
        for chro in self.plv["plot_chros"]:
            c_l = c_l_s[str(chro)]
            chr_b_s += int(c_l.get("size", 0))

        pyf = self.plv["plot_area_height"] * 0.5 / self.plv["plot_axis_y_max"]
        gaps = len(self.plv["plot_chros"]) - 1
        gap_sw = gaps * self.plv["plot_region_gap_width"]
        genome_width = paw - gap_sw
        b2pf = genome_width / chr_b_s  # TODO: only exists if using stack

        lab_f_s = round(self.plv["plot_samplestrip_height"] * 0.65, 1)
        if lab_f_s < self.plv["plot_labelcol_font_size"]:
            self.plv.update({"plot_labelcol_font_size": lab_f_s})

        self.plv.update({
            "styles": [
                f'.plot-area {{fill: {self.plv.get("plot_area_color", "#66ddff")}; fill-opacity: {self.plv.get("plot_area_opacity", 0.8)};}}',
                f'.title-left {{text-anchor: end; fill: {self.plv["plot_font_color"]}; font-size: {self.plv["plot_labelcol_font_size"]}px;}}'
            ],
            "Y": self.plv["plot_margins"],
            "plot_area_width": paw,
            "plot_area_x0": pax,
            "plot_area_xe": pax + paw,
            "plot_area_xc": pax + paw / 2,
            "plot_y2pf": pyf,
            "plot_genome_size": chr_b_s,
            "plot_b2pf": b2pf,
            "plot_labels": {},
            "dendrogram": False,
            "pls": []
        })

        prdbug(f'... done with {dbm}')

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __filter_empty_callsets_results(self):
        dbm = f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}'
        prdbug(dbm)

        if not "samplesplot" in self.plot_type:
            return

        p_t_s = self.plot_type_defs
        d_k = p_t_s["samplesplot"].get("data_key")

        if test_truthy(self.plv.get("plot_filter_empty_samples", False)):
            self.plot_data_bundle.update({d_k: [s for s in self.plot_data_bundle[d_k] if len(s['variants']) > 0]})

        self.plv.update({
            "results": self.plot_data_bundle[d_k],
            "results_number": len(self.plot_data_bundle[d_k])
        })


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_respond_empty_results(self):
        if self.plv["results_number"] > 0:
            return False
        
        dbm = f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}'
        prdbug(dbm)

        if self.plv["force_empty_plot"] is True:
            self.plv.update({"results": [{"variants":[]}]})
            return False

        self.plv.update({
            "plot_title_font_size": self.plv["plot_font_size"],
            "plot_title": "No matching CNV data"
        })

        self.__plot_add_title()

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __format_resultset_title(self):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        title = ""

        f_set = self.plv["results"][0]

        g_id = f_set.get("group_id")
        g_lab = f_set.get("label")
        if g_lab is not None:
            title = f"{g_lab}"
            if g_id is not None:
                title += f" ({g_id})"
        elif g_id is not None:
            title = g_id

        return title


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_title(self):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        # prdbug(f'font: {self.plv["plot_title_font_size"]}')
        # prdbug(f'title: {self.plv["plot_title"]}')

        if self.plv["plot_title_font_size"] < 1:
            return

        if len(self.plv.get("plot_title", "")) < 1:
            return

        self.plv["Y"] += self.plv["plot_title_font_size"]

        self.plv["pls"].append(
            '<text x="{}" y="{}" style="text-anchor: middle; font-size: {}px">{}</text>'.format(
                self.plv["plot_area_xc"],
                self.plv["Y"],
                self.plv["plot_title_font_size"],
                self.plv["plot_title"]
            )
        )
        self.plv["Y"] += self.plv["plot_title_font_size"]


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_cytobands(self):
        if self.plv["plot_chro_height"] < 1:
            return
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        chr_h = self.plv.get("plot_chro_height", 12)
        prg_w = self.plv.get("plot_region_gap_width", 2)

        self.__plot_add_cytoband_svg_gradients()

        # ------------------------- chromosome labels --------------------------#

        x = self.plv["plot_area_x0"]
        self.plv["Y"] += self.plv["plot_title_font_size"]

        for chro in self.plv["plot_chros"]:
            c_l = self.cytolimits.get(str(chro), {})

            chr_w = c_l["size"] * self.plv["plot_b2pf"]
            chr_c = x + chr_w / 2

            self.plv["pls"].append(
                f'<text x="{chr_c}" y="{self.plv["Y"]}" style="text-anchor: middle; font-size: {self.plv["plot_font_size"]}px">{chro}</text>')

            x += chr_w
            x += prg_w

        self.plv["Y"] += prg_w

        # ---------------------------- chromosomes ----------------------------#

        x = self.plv["plot_area_x0"]
        self.plv.update({"plot_chromosomes_y0": self.plv["Y"]})

        for chro in self.plv["plot_chros"]:

            c_l = self.cytolimits.get(str(chro), {})
            chr_w = c_l["size"] * self.plv["plot_b2pf"]

            chr_cb_s = list(filter(lambda d: d["chro"] == chro, self.cytobands.copy()))

            last = len(chr_cb_s) - 1
            this_n = 0

            for cb in chr_cb_s:

                this_n += 1
                s_b = cb["start"]
                e_b = cb["end"]
                c = cb["staining"]

                cb_l = int(e_b) - int(s_b)
                l_px = cb_l * self.plv["plot_b2pf"]

                by = self.plv["Y"]
                bh = chr_h

                if "cen" in c:
                    by += 0.2 * chr_h
                    bh -= 0.4 * chr_h
                elif "stalk" in c:
                    by += 0.3 * chr_h
                    bh -= 0.6 * chr_h
                elif this_n == 1 or this_n == last:
                    by += 0.1 * chr_h
                    bh -= 0.2 * chr_h

                self.plv["pls"].append(
                    f'<rect x="{round(x, 1)}" y="{round(by, 1)}" width="{round(l_px, 1)}" height="{round(bh, 1)}" style="fill: url(#{self.plv["plot_id"]}{c}); " />')

                x += l_px

            x += prg_w

        # -------------------------- / chromosomes -----------------------------#

        self.plv["Y"] += chr_h
        self.plv["Y"] += prg_w


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_cytoband_svg_gradients(self):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')

        c_defs = ""
        for cs_k, cs_c in self.plv["cytoband_shades"].items():
            p_id = self.plv.get("plot_id", "")
            c_defs += f'\n<linearGradient id="{p_id}{cs_k}" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">'
            for k, v in cs_c.items():
                c_defs += f'\n  <stop offset="{k}" stop-color="{v}" />'
            c_defs += f'\n</linearGradient>'

        self.plv["pls"].insert(0, c_defs)


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_samplestrips(self):
        if not "sample" in self.plot_type:
            return
        # prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')

        self.plv.update({"plot_first_area_y0": self.plv["Y"]})
        self.plv["pls"].append("")
        self.plv.update({"plot_strip_bg_i": len(self.plv["pls"]) - 1})

        if len(self.plv["results"]) > 0:
            self.__plot_order_samples()
            for s in self.plv["results"]:
                self.__plot_add_one_samplestrip(s)
                if self.plv["plot_labelcol_font_size"] > 5 and len(self.plv["results"]) > 1:
                    g_lab = self.__samplestrip_create_label(s)
                    self.__strip_add_left_label(g_lab)

        self.plv["plot_last_area_ye"] = self.plv["Y"]

        # ----------------------- plot cluster tree ---------------------------#

        self.plv.update({"cluster_head_gap": 0})
        self.plv.update({"plot_clusteritem_height": self.plv["plot_samplestrip_height"]})

        # --------------------- plot area background --------------------------#

        x_a_0 = self.plv["plot_area_x0"]
        p_a_w = self.plv["plot_area_width"]
        p_a_h = self.plv["Y"] - self.plv["plot_first_area_y0"]

        self.plv["pls"][self.plv[
            "plot_strip_bg_i"]] = f'<rect x="{x_a_0}" y="{self.plv["plot_first_area_y0"]}" width="{p_a_w}" height="{p_a_h}" class="plot-area" />'
        self.plv["Y"] += self.plv["plot_region_gap_width"]

    # -------------------------------------------------------------------------#

    def __samplestrip_create_label(self, sample):
        lab = ""
        label = sample.get("label", "")
        if len(bsl := sample.get("biosample_id", "")) > 3:
            bsl = f' - {bsl}'
        if len(asl := sample.get("analysis_id", "")) > 3:
            asl = f', {asl}'
        lab = f'{label}{bsl}{asl}'
        ds_lab = ""
        if len(self.plv["dataset_ids"]) > 1:
            if len(ds_lab := sample.get("dataset_id", "")) > 3:
                ds_lab = f' ({ds_lab})'
        return f'{lab}{ds_lab}'


    # -------------------------------------------------------------------------#

    def __strip_add_left_label(self, label):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        lab_x_e = self.plv["plot_area_x0"] - self.plv["plot_region_gap_width"] * 2
        self.plv["pls"].append(
            f'<text x="{lab_x_e}" y="{self.plv["Y"] - round(self.plv["plot_samplestrip_height"] * 0.2, 1)}" class="title-left">{label}</text>'
        )


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_order_samples(self):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')

        if self.plv.get("plot_cluster_results", True) is True and len(self.plv["results"]) > 2:
            dendrogram = cluster_samples(self.plv)
            new_order = dendrogram.get("leaves", [])
            if len(new_order) == len(self.plv["results"]):
                self.plv["results"][:] = [self.plv["results"][i] for i in dendrogram.get("leaves", [])]
                self.plv.update({"dendrogram": dendrogram})


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_one_samplestrip(self, s):
        x = self.plv["plot_area_x0"]
        h = self.plv["plot_samplestrip_height"]
        pvts = self.plv.get("plot_variant_types", {})

        col_c = {}
        for vt, cd in pvts.items():
            ck = cd.get("color_key", "___none___")
            col_c.update({vt: self.plv.get(ck, "rgb(111,111,111)")})

        v_s = s.get("variants", [])
        for chro in self.plv["plot_chros"]:
            c_l = self.cytolimits.get(str(chro), {})
            chr_w = c_l["size"] * self.plv["plot_b2pf"]
            c_v_s = list(filter(lambda d: d["location"]["chromosome"] == chro, v_s.copy()))
            for p_v in c_v_s:
                if "variant_state" in p_v:
                    t = p_v["variant_state"].get("id", "___none___")
                else:
                    t = p_v.get("variant_dupdel", "___none___")
                c = col_c.get(t, "rgb(111,111,111)")

                if "location" in p_v:
                    s_v = int(p_v["location"].get("start", 0))
                    e_v = int(p_v["location"].get("end", s_v + 1))
                else:
                    s_v = int(p_v.get("start", 0))
                    e_v = int(p_v.get("end", s_v + 1))
                l = round((e_v - s_v) * self.plv["plot_b2pf"], 1)
                if l < 0.5:
                    l = 0.5
                s = round(x + s_v * self.plv["plot_b2pf"], 1)           

                self.plv["pls"].append(
                    f'<rect x="{s}" y="{self.plv["Y"]}" width="{l}" height="{h}" style="fill: {c} " />')

            x += chr_w
            x += self.plv["plot_region_gap_width"]

        self.plv["Y"] += h


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_cluster_tree(self):
        d = self.plv.get("dendrogram", False)
        if d is False:
            return
        if self.plv.get("plot_dendrogram_width", 0) < 1:
            return
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')

        ci_h = self.plv["plot_clusteritem_height"]
        cl_h_g = self.plv.get("cluster_head_gap", 2)
        p_s_c = self.plv.get("plot_dendrogram_color", '#ee0000')
        p_s_w = self.plv.get("plot_dendrogram_stroke", 1)

        d_x_s = d.get("dcoord", [])
        d_y_s = d.get("icoord", [])

        t_y_0 = self.plv["plot_first_area_y0"]
        t_x_0 = self.plv["plot_area_x0"] + self.plv["plot_area_width"]
        t_y_f = ci_h * 0.1

        x_max = self.plv["plot_dendrogram_width"]

        # finding the largest x-value of the dendrogram for scaling
        for i, node in enumerate(d_x_s):
            for j, x in enumerate(node):
                if x > x_max:
                    x_max = x
        t_x_f = self.plv["plot_dendrogram_width"] / x_max

        for i, node in enumerate(d_x_s):

            n = f'<polyline points="'

            for j, x in enumerate(node):
                y = d_y_s[i][j] * t_y_f - cl_h_g

                for h, f_set in enumerate(self.plv["results"]):
                    h_y_e = h * (ci_h + cl_h_g)
                    if y > h_y_e:
                        y += cl_h_g

                n += f' {round(t_x_0 + x * t_x_f, 1)},{round(t_y_0 + y, 1)}'

            n += f'" fill="none" stroke="{p_s_c}" stroke-width="{p_s_w}px" />'

            self.plv["pls"].append(n)


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_histodata(self):
        if "histo" not in self.plot_type:
            return
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')

        self.plv.update({"plot_first_area_y0": self.plv["Y"]})

        s_no = 0
        for f_set in self.plv["results"]:
            s_no += f_set.get("sample_count", 0)
        if s_no > 0:
            self.plv.update({"sample_count": s_no})

        self.__plot_order_histograms()
        if "heat" in self.plot_type:
            self.plv.update({"cluster_head_gap": 0})
            self.plv.update({"plot_clusteritem_height": self.plv["plot_samplestrip_height"]})
            for f_set in self.plv["results"]:
                self.__plot_draw_one_heatstrip(f_set)
        else:
            self.plv.update({"cluster_head_gap": self.plv["plot_region_gap_width"]})
            self.plv.update({"plot_clusteritem_height": self.plv["plot_area_height"]})
            for f_set in self.plv["results"]:
                self.__plot_add_one_histogram(f_set)

        self.plv["plot_last_area_ye"] = self.plv["Y"]


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_order_histograms(self):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        if self.plv.get("plot_cluster_results", True) is True and len(self.plv["results"]) > 2:
            dendrogram = cluster_frequencies(self.plv)
            new_order = dendrogram.get("leaves", [])
            if len(new_order) == len(self.plv["results"]):
                self.plv["results"][:] = [self.plv["results"][i] for i in dendrogram.get("leaves", [])]
                self.plv.update({"dendrogram": dendrogram})


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_one_histogram(self, f_set):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')

        self.__plot_add_one_histogram_canvas(f_set)

        i_f = f_set.get("interval_frequencies", [])
        x = self.plv["plot_area_x0"]
        h_y_0 = self.plv["Y"] + self.plv["plot_area_height"] * 0.5

        # ------------------------- histogram data -----------------------------#

        # TODO: in contrast to the Perl version here we don't correct for interval
        #       sets which _do not_ correspond to the full chromosome coordinates

        cnv_c = {
            "gain_frequency": self.plv["plot_dup_color"],
            "loss_frequency": self.plv["plot_del_color"],
            "gain_hlfrequency": self.plv["plot_hldup_color"],
            "loss_hlfrequency": self.plv["plot_hldel_color"]
        }
        # just to have + / - direction by key
        cnv_f = {
            "gain_frequency": -1,
            "gain_hlfrequency": -1,
            "loss_frequency": 1,
            "loss_hlfrequency": 1
        }

        for chro in self.plv["plot_chros"]:

            c_l = self.cytolimits.get(str(chro), {})
            chr_w = c_l["size"] * self.plv["plot_b2pf"]

            c_i_f = list(filter(lambda d: d["reference_name"] == chro, i_f.copy()))
            c_i_no = len(c_i_f)

            # here w/ given order for overplotting the HL ones ...
            for GL in ["gain_frequency", "gain_hlfrequency", "loss_frequency", "loss_hlfrequency"]:

                p_c = cnv_c[GL]
                h_f = cnv_f[GL]

                p = f'<polygon points="{round(x, 1)},{round(h_y_0, 1)}'

                i_x_0 = x
                prev = -1
                for c_i_i, i_v in enumerate(c_i_f, start=1):

                    prdbug(i_v)

                    s = i_x_0 + i_v.get("start", 0) * self.plv["plot_b2pf"]
                    e = i_x_0 + i_v.get("end", 0) * self.plv["plot_b2pf"]
                    v = i_v.get(GL, 0)
                    h = v * self.plv["plot_y2pf"]
                    h_p = h_y_0 + h * h_f

                    point = f' {round(s, 1)},{round(h_p, 1)}'

                    # This construct avoids adding intermediary points w/ the same
                    # value as the one before and after 
                    if c_i_no > c_i_i:
                        future = c_i_f[c_i_i].get(GL, 0)
                        if prev != v or future != v:
                            p += point
                    else:
                        p += point

                    prev = v

                p += f' {round((x + chr_w), 1)},{round(h_y_0, 1)}" fill="{p_c}" stroke-width="0px" />'
                self.plv["pls"].append(p)

            x += chr_w
            x += self.plv["plot_region_gap_width"]

        # ------------------------ / histogram data ---------------------------#

        self.plv["Y"] += self.plv["plot_area_height"]
        self.plv.update({"plot_last_area_ye": self.plv["Y"]})
        self.plv["Y"] += self.plv["plot_region_gap_width"]


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_draw_one_heatstrip(self, f_set):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')

        i_f = f_set.get("interval_frequencies", [])

        x = 0
        h = self.plv["plot_samplestrip_height"]

        image = Image.new(
                    'RGBA',
                    (self.plv["plot_area_width"], h),
                    color=self.plv["plot_area_color"]
                )
        draw = ImageDraw.Draw(image)

        # ------------------------- frequency data ----------------------------#

        g_c = self.plv["plot_dup_color"]
        l_c = self.plv["plot_del_color"]

        for chro in self.plv["plot_chros"]:

            c_l = self.cytolimits.get(str(chro), {})
            chr_w = c_l["size"] * self.plv["plot_b2pf"]

            c_i_f = list(filter(lambda d: d["reference_name"] == chro, i_f.copy()))
            c_i_c = []
            for i_v in c_i_f:
                g_f = i_v.get("gain_frequency", 0)
                l_f = i_v.get("loss_frequency", 0)
                c = self.__mix_frequencies_2_rgb(g_f, l_f, 50)
                c_i_c.append({
                    "start": int(i_v.get("start", 0)),
                    "end": int(i_v.get("end", 0)),
                    "fill": c
                })

            s_s = c_i_c[0].get("start")
            # iterating over all but the last entry; c_i_i is index for next entry 
            for c_i_i, p_v in enumerate(c_i_c[:-1], start=1):
                s_e = p_v.get("end")
                f_c = c_i_c[c_i_i].get("fill")
                c = p_v.get("fill")
                if f_c != c:
                    s = round(x + s_s * self.plv["plot_b2pf"], 1)
                    e = round(x + s_e * self.plv["plot_b2pf"], 1)
                    draw.rectangle([s, 0, e, h], fill=c)

                    # plot start is reset to the next interval start
                    s_s = c_i_c[c_i_i].get("start")

            # last interval
            s = round(x + s_s * self.plv["plot_b2pf"], 1)
            e = round(x + c_i_c[-1].get("end") * self.plv["plot_b2pf"], 1)
            c = c_i_c[-1].get("fill")
            draw.rectangle([s, 0, e, h], fill=c)

            x += chr_w
            x += self.plv["plot_region_gap_width"]

        # ------------------------ / histoheat data ---------------------------#

        in_mem_file = io.BytesIO()
        image.save(in_mem_file, format = "PNG")
        in_mem_file.seek(0)
        img_bytes = in_mem_file.read()
        base64_encoded_result_bytes = base64.b64encode(img_bytes)
        base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')

        self.plv["pls"].append("""
<image
  x="{}"
  y="{}"
  width="{}"
  height="{}"
  xlink:href="data:image/png;base64,{}"
/>""".format(
            self.plv["plot_area_x0"],
            self.plv["Y"],
            self.plv["plot_area_width"],
            h,
            base64_encoded_result_str
        ))

        self.plv["Y"] += h

        g_id = f_set.get("group_id", "NA")
        g_lab = f_set.get("label", g_id)
        g_ds_id = f_set.get("dataset_id", False)
        g_no = f_set.get("sample_count", 0)

        # The condition splits the label data on 2 lines if a text label pre-exists
        if len(self.plv["dataset_ids"]) > 1 and g_ds_id is not False:
            g_lab = f'{g_id} ({g_ds_id}, {g_no} {"samples" if g_no > 1 else "sample"})'
        else:
            g_lab = f'{g_id} ({g_no} {"samples" if g_no > 1 else "sample"} )'

        self.__strip_add_left_label(g_lab)


    # -------------------------------------------------------------------------#

    def __mix_frequencies_2_rgb(self, gain_f, loss_f, max_f=80):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        rgb = [127, 127, 127]
        h_i = self.plv.get("plot_heat_intensity", 1)
        if h_i < 0.1:
            h_i = 0.1
        f_f = max_f / self.plv.get("plot_heat_intensity", 1)
        dup_rgb = list(ImageColor.getcolor(self.plv["plot_dup_color"], "RGB"))
        del_rgb = list(ImageColor.getcolor(self.plv["plot_del_color"], "RGB"))
        for i in (0,1,2):
            dup_rgb[i] = int(dup_rgb[i] * gain_f / f_f)
            del_rgb[i] = int(del_rgb[i] * loss_f / f_f)
            rgb[i] = dup_rgb[i] + del_rgb[i]
            if rgb[i] > 255:
                rgb[i] = 255
            rgb[i] = str(rgb[i])

        return f'rgb({",".join(rgb)})'


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_one_histogram_canvas(self, f_set):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        x_a_0 = self.plv["plot_area_x0"]
        p_a_w = self.plv["plot_area_width"]
        p_a_h = self.plv["plot_area_height"]

        # -------------------------- left labels ------------------------------#

        self.__histoplot_add_left_label(f_set)

        # --------------------- plot area background --------------------------#

        self.plv["pls"].append(
            f'<rect x="{x_a_0}" y="{self.plv["Y"]}" width="{p_a_w}" height="{p_a_h}" class="plot-area" />')

        # --------------------------- grid lines ------------------------------#

        self.__plot_area_add_grid()


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __histoplot_add_left_label(self, f_set):
        if self.plv["plot_labelcol_width"] < 10:
            return
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        lab_x_e = self.plv["plot_margins"] + self.plv["plot_labelcol_width"]
        h_y_0 = self.plv["Y"] + self.plv["plot_area_height"] * 0.5
        self.plv["styles"].append(
            f'.title-left {{text-anchor: end; fill: {self.plv["plot_font_color"]}; font-size: {self.plv["plot_labelcol_font_size"]}px;}}'
        )
        g_id = f_set.get("group_id", "NA")
        g_ds_id = f_set.get("dataset_id", False)
        g_lab = f_set.get("label", "")
        g_no = f_set.get("sample_count", 0)

        # The condition splits the label data on 2 lines if a text label pre-exists
        if len(self.plv["dataset_ids"]) > 1 and g_ds_id is not False:
            count_lab = f' ({g_ds_id}, {g_no} {"samples" if g_no > 1 else "sample"})'
        else:
            count_lab = f' ({g_no} {"samples" if g_no > 1 else "sample"} )'
        if len(g_lab) > 0:
            lab_y = h_y_0 - self.plv["plot_labelcol_font_size"] * 0.2
            self.plv["pls"].append(f'<text x="{lab_x_e}" y="{lab_y}" class="title-left">{g_lab}</text>')
            lab_y = h_y_0 + self.plv["plot_labelcol_font_size"] * 1.2
            self.plv["pls"].append(f'<text x="{lab_x_e}" y="{lab_y}" class="title-left">{g_id}{count_lab}</text>')
        else:
            lab_y = h_y_0 - self.plv["plot_labelcol_font_size"] * 0.5
            self.plv["pls"].append(f'<text x="{lab_x_e}" y="{lab_y}" class="title-left">{g_id}{count_lab}</text>')


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_area_add_grid(self):
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        x_a_0 = self.plv["plot_area_x0"]
        x_c_e = self.plv["plot_area_xe"]
        h_y_0 = self.plv["Y"] + self.plv["plot_area_height"] * 0.5
        x_y_l = x_a_0 - self.plv["plot_region_gap_width"]
        u = self.plv["plot_label_y_unit"]
        self.plv["styles"].append(
            f'.label-y {{text-anchor: end; fill: {self.plv["plot_label_y_font_color"]}; font-size: {self.plv["plot_label_y_font_size"]}px;}}'
        )
        self.plv["styles"].append(
            f'.gridline {{stroke-width: {self.plv["plot_grid_stroke"]}px; stroke: {self.plv["plot_grid_color"]}; opacity: {self.plv["plot_grid_opacity"]} ; }}',
        )

        # -------------------------- center line ------------------------------#

        self.plv["pls"].append(
            f'<line x1="{x_a_0 - self.plv["plot_region_gap_width"] - self.plv["plot_axislab_y_width"]}"  y1="{h_y_0}"  x2="{x_c_e}"  y2="{h_y_0}" class="gridline" />')

        # --------------------------- grid lines ------------------------------#

        for y_m in self.plv["plot_label_y_values"]:

            if y_m >= self.plv["plot_axis_y_max"]:
                continue

            for f in [1, -1]:
                if u == "" and f == 1:
                    neg = "-"
                else:
                    neg = ""

                y_v = h_y_0 + f * y_m * self.plv["plot_y2pf"]
                y_l_y = y_v + self.plv["plot_label_y_font_size"] / 2

                self.plv["pls"].append(f'<line x1="{x_a_0}" y1="{y_v}" x2="{x_c_e}" y2="{y_v}" class="gridline" />')

                if self.plv["plot_axislab_y_width"] < 10:
                    continue

                self.plv["pls"].append(f'<text x="{x_y_l}" y="{y_l_y}" class="label-y">{neg}{y_m}{u}</text>')


    # -------------------------------------------------------------------------#
    # --------------------------- probesplot ----------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_probesplot(self):
        """
        Prototyping bitmap drawing for probe plots etc.
        Invoked w/ &plotType=probesplot
        https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html
        
        #### Draw examples

        * draw.point((50,50), (50,255,0))
        * draw.line((0, 0) + image.size, fill=128)
        * draw.line((0, image.size[1], image.size[0], 0), fill=(50,255,0))
        * draw.rectangle([0, 0, 28, image.size[1]], fill="rgb(255,20,66)")
        * draw.ellipse([(80,20),(130,50)], fill="#ccccff", outline="red")
        
        #### Input:
        ```
        probes = [
            {
                "reference_name": "17",
                "start": 13663925,
                "value": 2.5
            },
            {...}
        ]
        ```
        """

        if not "probesplot" in self.plot_type:
            return
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')

        p_t_s = self.plot_type_defs
        d_k = p_t_s["probesplot"].get("data_key")

        probebundles = self.plot_data_bundle.get(d_k, [{"id":"___undefined___"}])
        if len(probebundles) != 1:
            return
        if not "cn_probes" in probebundles[0]:
            return

        probes = probebundles[0].get("cn_probes", [])
        self.plv.update({
            "plot_axis_y_max": 4,
            "plot_y2pf": self.plv["plot_area_height"] * 0.5 / 4 * self.plv["plot_probe_y_factor"],
            "plot_first_area_y0": self.plv["Y"],
            "plot_label_y_unit": "",
            "plot_label_y_values": self.plv["plot_probe_label_y_values"]
        })

        x = 0
        h_y_0 = self.plv["plot_area_height"] * 0.5
        p_y_f = self.plv["plot_y2pf"]
        p_half = self.plv["plot_probedot_size"] * 0.5
        p_dense = self.plv["plot_probedot_opacity"]

        if len(probes) > 500000:
            p_half *= 0.5
            p_dense = p_dense * 0.7
        p_dense = int(round(p_dense, 0))

        image = Image.new(
                    'RGBA',
                    (self.plv["plot_area_width"], self.plv["plot_area_height"]),
                    color=self.plv["plot_area_color"]
                )
        draw = ImageDraw.Draw(image)

        for chro in self.plv["plot_chros"]:

            c_p = list(filter(lambda d: d["reference_name"] == chro, probes.copy()))
            c_l = self.cytolimits.get(str(chro), {})
            chr_w = c_l["size"] * self.plv["plot_b2pf"]

            for i_v in c_p:
                s = x + i_v.get("start", 0) * self.plv["plot_b2pf"]
                v = i_v.get("value", 0)
                h = v * p_y_f 
                if h > h_y_0:
                    h = h_y_0
                if h < -h_y_0:
                    h = -h_y_0
                h_p = h_y_0 - h

                # draw.ellipse(
                #     [
                #         (s-p_half, h_p - p_half),
                #         (s+p_half, h_p + p_half)
                #     ],
                #     fill=(0,0,63,p_dense)
                # )
                draw.point((round(s, 2),round(h_p, 2)), (0,0,63,p_dense))

            x += chr_w + self.plv["plot_region_gap_width"]

        # ------------------------ / histogram data ---------------------------#

        in_mem_file = io.BytesIO()
        image.save(in_mem_file, format = "PNG")
        in_mem_file.seek(0)
        img_bytes = in_mem_file.read()
        base64_encoded_result_bytes = base64.b64encode(img_bytes)
        base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')

        self.plv["pls"].append("""
<image
  x="{}"
  y="{}"
  width="{}"
  height="{}"
  xlink:href="data:image/png;base64,{}"
/>""".format(
            self.plv["plot_area_x0"],
            self.plv["Y"],
            self.plv["plot_area_width"],
            self.plv["plot_area_height"],
            base64_encoded_result_str
        ))

        self.__plot_area_add_grid()
        self.plv["Y"] += self.plv["plot_area_height"]
        self.plv.update({"plot_last_area_ye": self.plv["Y"]})
        self.plv["Y"] += self.plv["plot_region_gap_width"]

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_markers(self):
        self.__add_labs_from_plot_region_labels()
        self.__add_labs_from_gene_symbols()
        self.__add_labs_from_cytobands()
        labs = self.plv.get("plot_labels", [])
        if len(labs) < 1:
            return
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        b2pf = self.plv["plot_b2pf"]
        x = self.plv["plot_area_x0"]
        p_m_f_s = self.plv["plot_marker_font_size"]
        p_m_l_p = self.plv["plot_marker_label_padding"]
        p_m_lane_p = self.plv["plot_marker_lane_padding"]
        p_m_l_h = p_m_f_s + p_m_l_p * 2
        p_m_lane_h = p_m_l_h + p_m_lane_p
        max_lane = 0
        marker_y_0 = round(self.plv["plot_first_area_y0"], 1)
        marker_y_e = round(self.plv["plot_last_area_ye"] + p_m_lane_p, 1)
        m_p_e = [(x - 30)]
        for chro in self.plv["plot_chros"]:
            c_l = self.cytolimits.get(str(chro), {})
            chr_w = c_l["size"] * self.plv["plot_b2pf"]
            for m_k, m_v in labs.items():
                c = str(m_v.get("chro", "__na__"))
                if str(chro) != c:
                    continue
                s = int(m_v.get("start", 0))
                e = int(m_v.get("end", 0))
                label = m_v.get("label", "")
                color = m_v.get("color", "#dddddd")
                m_s = x + s * b2pf
                m_e = x + e * b2pf
                m_w = m_e - m_s
                if 1 > m_w > 0:
                    m_w = 1
                else:
                    m_w = round(m_w, 1)
                m_c = round((m_s + m_e) / 2, 1)
                m_l_w = len(label) * 0.75 * p_m_f_s
                m_l_s = m_c - 0.5 * m_l_w
                m_l_e = m_c + 0.5 * m_l_w
                found_space = False
                l_i = 0
                for p_e in m_p_e:
                    if m_l_s > p_e:
                        found_space = True
                        m_p_e[l_i] = m_l_e
                        break
                    l_i += 1
                if found_space is False:
                    m_p_e.append(m_l_e)
                if len(m_p_e) > max_lane:
                    max_lane = len(m_p_e)
                m_y_e = marker_y_e + l_i * p_m_lane_h
                m_h = round(m_y_e - marker_y_0, 1)
                l_y_p = marker_y_e + l_i * p_m_lane_h + p_m_lane_h - p_m_l_p - p_m_lane_p - 1

                self.plv["pls"].append(
                    f'<rect x="{round(m_s, 1)}" y="{marker_y_0}" width="{round(m_w, 1)}" height="{m_h}" class="marker" style="fill: {color}; opacity: 0.4; " />')
                self.plv["pls"].append(
                    f'<rect x="{round(m_l_s, 1)}" y="{m_y_e}" width="{round(m_l_w, 1)}" height="{p_m_l_h}" class="marker" style="fill: {color}; opacity: 0.1; " />')
                self.plv["pls"].append(f'<text x="{m_c}" y="{l_y_p}" class="marker">{label}</text>')

            x += chr_w
            x += self.plv["plot_region_gap_width"]

        # --------------------- end chromosome loop ---------------------------#

        if max_lane > 0:
            self.plv["Y"] += max_lane * p_m_lane_h
            self.plv["Y"] += self.plv["plot_region_gap_width"]
            self.plv["styles"].append(
                f'.marker {{text-anchor: middle; fill: {self.plv["plot_marker_font_color"]}; font-size: {p_m_f_s}px;}}'
            )


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __add_labs_from_plot_region_labels(self):
        r_l_s = self.plv.get("plot_region_labels", [])
        if len(r_l_s) < 1:
            return
        prdbug(f'{inspect.stack()[1][3]} from {inspect.stack()[2][3]}')
        for label in r_l_s:
            l_i = re.split(":", label)
            if len(l_i) < 2:
                continue
            c = l_i.pop(0)
            s_e_i = l_i.pop(0)
            s_e = re.split("-", s_e_i)
            s = s_e.pop(0)
            if not re.match(r'^\d+?$', str(s)):
                continue
            if len(s_e) < 1:
                e = str(int(s) + 1)
            else:
                e = s_e.pop(0)

            if len(l_i) > 0:
                label = str(l_i.pop(0))
            else:
                label = ""

            l_c = self.plv.get("plot_regionlabel_color", "#dddddd")
            m = self.__make_marker_object(c, s, e, l_c, label)

            self.plv["plot_labels"].update(m)


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __add_labs_from_gene_symbols(self):
        GI = GeneInfo()
        g_s_s = self.plv.get("plot_gene_symbols", [])
        if len(g_s_s) < 1:
            return
        g_l = []
        for q_g in g_s_s:
            genes = GI.returnGene(q_g)          # list of one exact match   
            if len(genes) > 0:
                g_l += genes
        for f_g in g_l:
            m = self.__make_marker_object(
                f_g.get("reference_name", False),
                f_g.get("start", False),
                f_g.get("end", False),
                self.plv.get("plot_marker_font_color", "#ccccff"),
                f_g.get("symbol", False)
            )
            if m:
                self.plv["plot_labels"].update(m)
        prdbug(self.plv["plot_labels"])


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __add_labs_from_cytobands(self):
        g_s_s = self.plv.get("plot_cytoregion_labels", [])
        if len(g_s_s) < 1:
            return
        g_l = []
        for q_g in g_s_s:
            cytoBands, chro, start, end, error = bands_from_cytobands(q_g)
            if len(cytoBands) < 1:
                continue
            m = self.__make_marker_object(
                chro,
                start,
                end,
                self.plv.get("plot_cytoregion_color", "#ccccff"),
                q_g
            )
            if m is not None:
                self.plv["plot_labels"].update(m)

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __make_marker_object(self, chromosome, start, end, color, label=""):
        prdbug(f'label color: {color}')
        m = None

        # Checks here or upstream?
        # Cave: `any` ... `is False` to avoid `True` for `0` with `False in`
        if any(x is False for x in [chromosome, start, end, label]):
            return m
        m_k = f'{chromosome}:{start}-{end}:{label}'
        m = {
            m_k: {
                "chro": chromosome,
                "start": start,
                "end": end,
                "label": label,
                "color": color
            }
        }
        return m


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __plot_add_footer(self):
        today = date.today()
        x_a_0 = self.plv["plot_area_x0"]
        x_c_e = x_a_0 + self.plv["plot_area_width"]
        self.plv["styles"].append(
            f'.footer-r {{text-anchor: end; fill: {self.plv["plot_footer_font_color"]}; font-size: {self.plv["plot_footer_font_size"]}px;}}'
        )
        self.plv["styles"].append(
            f'.footer-l {{text-anchor: start; fill: {self.plv["plot_footer_font_color"]}; font-size: {self.plv["plot_footer_font_size"]}px;}}'
        )
        self.plv["Y"] += self.plv["plot_footer_font_size"]
        self.plv["pls"].append(
            f'<text x="{x_c_e}" y="{self.plv["Y"]}" class="footer-r">&#169; CC-BY 2001 - {today.year} progenetix.org</text>')

        if self.plv.get("sample_count", 0) > 1:
            self.plv["pls"].append(
                f'<text x="{x_a_0}" y="{self.plv["Y"]}" class="footer-l">{self.plv["sample_count"]} {self.plv["data_type"]}</text>')

        self.plv["Y"] += self.plv["plot_margins"]


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __create_svg(self):

        svg = """<svg
xmlns="http://www.w3.org/2000/svg"
xmlns:xlink="http://www.w3.org/1999/xlink"
version="1.1"
id="{}"
width="{}px"
height="{}px"
style="margin: auto; font-family: Helvetica, sans-serif;">
<style type="text/css"><![CDATA[
{}
]]></style>
<rect x="0" y="0" width="{}" height="{}" style="fill: {}" />
{}
</svg>""".format(
            self.plv["plot_id"],
            self.plv["plot_width"],
            self.plv["Y"],
            "\n  ".join(self.plv["styles"]),
            self.plv["plot_width"],
            self.plv["Y"],
            self.plv["plot_canvas_color"],
            "\n".join(self.plv["pls"])
        )

        return svg

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __print_svg_response(self):
        if not "local" in ENV:
            print('Content-Type: image/svg+xml')
            print('status: 200')
            print()
            print()

        print(self.svg)
        print()
        exit()

################################################################################
################################################################################
################################################################################


