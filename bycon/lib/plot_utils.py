import re
import datetime
from urllib.parse import unquote
from cgi_parsing import get_plot_parameters, print_svg_response, test_truthy
from cytoband_utils import bands_from_cytobands, retrieve_gene_id_coordinates
from clustering_utils import cluster_frequencies, cluster_samples
from response_remapping import de_vrsify_variant, callsets_create_iset

# http://progenetix.org/cgi/bycon/services/intervalFrequencies.py?chr2plot=8,9,17&labels=8:120000000-123000000:Some+Interesting+Region&plot_gene_symbols=MYCN,REL,TP53,MTAP,CDKN2A,MYC,ERBB2,CDK1&filters=pgx:icdom-85003&output=histoplot
# http://progenetix.org/beacon/biosamples/?datasetIds=examplez,progenetix,cellz&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&output=histoplot&plotGeneSymbols=CDKN2A,MTAP,EGFR,BCL6

################################################################################

def histoplot_svg_generator(byc, results):

    svg = False
    if not "histoplot" in byc["output"]:
        return svg

    plv = _initialize_plot_values(byc, results)
    if _plot_respond_empty_results(plv, byc) is not False:
        svg = _create_svg(plv)
        return svg

    _plot_add_title(plv, byc)
    _plot_add_cytobands(plv, byc)
    _plot_add_histodata(plv, byc)
    _plot_add_markers(plv, byc)
    _plot_add_footer(plv, byc)

    plv["Y"] += plv["plot_margins"]

    #--------------------------------------------------------------------------#

    svg = _create_svg(plv)
    return svg

################################################################################

def samplesplot_svg_generator(byc, results):

    svg = False
    if not "samplesplot" in byc["output"]:
        return svg

    plv = _initialize_plot_values(byc, results)

    if test_truthy(plv.get("plot_filter_empty_samples", False)):
        results = [s for s in results if len(s['variants']) > 0] 

    if _plot_respond_empty_results(plv, byc) is not False:
        svg = _create_svg(plv)
        return svg

    _plot_add_title(plv, byc)
    _plot_add_cytobands(plv, byc)
    _plot_add_samplestrips(plv, byc)
    _plot_add_markers(plv, byc)
    _plot_add_footer(plv, byc)

    plv["Y"] += plv["plot_margins"]

    #--------------------------------------------------------------------------#

    svg = _create_svg(plv)
    return svg

################################################################################

def _initialize_plot_values(byc, results):

    p_d_p = byc["plot_defaults"]["parameters"]
    r_no = len(results)

    plv = {
        "pls": [],
        "results_number": r_no,
        "cytoband_shades": byc["plot_defaults"].get("cytoband_shades", {})
    }

    for p_k, p_d in p_d_p.items():
        if "default" in p_d:
            plv.update({ p_k: p_d["default"] })
        else:
            plv.update({ p_k: "" })

    if plv["results_number"] < 2:
        plv.update({ "plot_labelcol_width": 0 })

    if plv["results_number"] > 2:
        plv.update({ "plot_cluster_results": True })
    else:
        plv.update({ "plot_dendrogram_width": 0 })

    get_plot_parameters(plv, byc)

    pax = plv["plot_margins"] + plv["plot_labelcol_width"] + plv["plot_axislab_y_width"]

    paw = plv["plot_width"] - 2 * plv["plot_margins"]
    paw -= plv["plot_labelcol_width"]
    paw -= plv["plot_axislab_y_width"]
    paw -= plv["plot_dendrogram_width"]

    # calculate the base
    chr_b_s = 0
    for chro in plv["plot_chros"]:
        c_l = byc["cytolimits"][chro]
        chr_b_s += c_l["size"]

    pyf = plv["plot_area_height"] * 0.5 / plv["plot_axis_y_max"]

    gaps = len(plv["plot_chros"]) - 1
    gap_sw = gaps * plv["plot_region_gap_width"]
    genome_width = paw - gap_sw
    b2pf = genome_width / chr_b_s # TODO: only exists if using stack

    title = plv.get("plot_title", "")
    if len(title) < 3:
        if plv["results_number"] == 1:
            title = _format_resultset_title(results[0])

    plv.update({
        "results": results,
        "plot_title": title,
        "styles": [ f'.plot-area {{fill: { plv.get("plot_area_color", "#66ddff") }; fill-opacity: { plv.get("plot_area_opacity", 0.8) };}}' ],
        "Y": plv["plot_margins"],
        "plot_area_width": paw,
        "plot_area_x0": pax,
        "plot_area_xe": pax + paw,
        "plot_area_xc": pax + paw / 2,
        "plot_y2pf": pyf,
        "plot_genome_size": chr_b_s,
        "plot_b2pf": b2pf,
        "plot_labels": {},
        "dendrogram": False
    })

    return plv

################################################################################

def _plot_respond_empty_results(plv, byc):
    
    if len(plv["results"]) > 0:
        return False

    plv.update({
            "plot_title_font_size": plv["plot_font_size"],
            "plot_title": "No matching CNV data"
    })

    _plot_add_title(plv, byc)
    _plot_add_footer(plv, byc)

    return plv

################################################################################

def _format_resultset_title(f_set):

    g_id = f_set.get("group_id", "NA")
    g_lab = f_set.get("label", "")
    if len(g_lab) > 1:
        title = "{} ({})".format(g_lab, g_id)
    else:
        title = g_id

    return title

################################################################################

def _plot_add_title(plv, byc):

    if len(plv.get("plot_title", "")) < 3:
        return plv

    t_l = len(plv["plot_title"]) * 0.45 * plv["plot_title_font_size"]
    plv["Y"] += plv["plot_title_font_size"]

    plv["pls"].append(
'<text x="{}" y="{}" style="text-anchor: middle; font-size: {}px">{}</text>'.format(
            plv["plot_area_xc"],
            plv["Y"],
            plv["plot_title_font_size"],
            plv["plot_title"]
        )
    )

    plv["Y"] += plv["plot_title_font_size"]

    return plv

################################################################################

def _plot_add_cytobands(plv, byc):

    if plv["plot_chro_height"] < 1:
        return plv

    _plot_add_cytoband_svg_gradients(plv)

    #------------------------- chromosome labels ------------------------------#

    X = plv["plot_area_x0"]
    plv["Y"] += plv["plot_title_font_size"]

    for chro in plv["plot_chros"]:

        c_l = byc["cytolimits"][str(chro)]

        chr_w = c_l["size"] * plv["plot_b2pf"]
        chr_c = X + chr_w / 2

        plv["pls"].append(f'<text x="{chr_c}" y="{plv["Y"]}" style="text-anchor: middle; font-size: {plv["plot_font_size"]}px">{chro}</text>')

        X += chr_w
        X += plv["plot_region_gap_width"]

    plv["Y"] += plv["plot_region_gap_width"]

    #---------------------------- chromosomes ---------------------------------#

    X = plv["plot_area_x0"]
    plv.update({"plot_chromosomes_y0": plv["Y"]})

    for chro in plv["plot_chros"]:

        c_l = byc["cytolimits"][str(chro)]
        chr_w = c_l["size"] * plv["plot_b2pf"]

        chr_cb_s = list(filter(lambda d: d[ "chro" ] == chro, byc["cytobands"].copy()))

        last = len(chr_cb_s) - 1
        this_n = 0

        for cb in chr_cb_s:

            this_n += 1

            s_b = cb["start"]
            e_b = cb["end"]
            c = cb["staining"]
            l = int(e_b) - int(s_b)
            l_px = l * plv["plot_b2pf"]

            by = plv["Y"]
            bh = plv["plot_chro_height"]

            if "cen" in c:
                by += 0.2 * plv["plot_chro_height"]
                bh -= 0.4 * plv["plot_chro_height"]
            elif "stalk" in c:
                by += 0.3 * plv["plot_chro_height"]
                bh -= 0.6 * plv["plot_chro_height"]
            elif this_n == 1 or this_n == last:
                by += 0.1 * plv["plot_chro_height"]
                bh -= 0.2 * plv["plot_chro_height"]

            plv["pls"].append(f'<rect x="{round(X, 1)}" y="{round(by, 1)}" width="{round(l_px, 1)}" height="{round(bh, 1)}" style="fill: url(#{plv["plot_id"]}{c}); " />')

            X += l_px

        X += plv["plot_region_gap_width"]

    #-------------------------- / chromosomes ---------------------------------#

    plv["Y"] += plv["plot_chro_height"]
    plv["Y"] += plv["plot_region_gap_width"]

    return plv

################################################################################

def _plot_add_histodata(plv, byc):

    plv.update( {"plot_first_area_y0": plv["Y"] })

    _plot_order_histograms(plv, byc)

    for f_set in plv["results"]:
        _plot_add_one_histogram(plv, f_set, byc)

    plv["plot_last_histo_ye"] = plv["Y"]

    #----------------------- plot cluster tree --------------------------------#

    plv.update({"cluster_head_gap": plv["plot_region_gap_width"]})
    _plot_add_cluster_tree(plv, plv["plot_area_height"], byc)

    return plv

################################################################################

def _plot_order_histograms(plv, byc):

    if plv.get("plot_cluster_results", True) is True and len(plv["results"]) > 2:
        dendrogram = cluster_frequencies(plv, byc)
        new_order = dendrogram.get("leaves", [])
        if len(new_order) == len(plv["results"]):
            plv["results"][:] = [ plv["results"][i] for i in dendrogram.get("leaves", []) ]
            plv.update({"dendrogram": dendrogram})

    return plv

###############################################################################

def _plot_order_samples(plv, byc):

    if plv.get("plot_cluster_results", True) is True and len(plv["results"]) > 2:
        dendrogram = cluster_samples(plv, byc)
        new_order = dendrogram.get("leaves", [])
        if len(new_order) == len(plv["results"]):
            plv["results"][:] = [ plv["results"][i] for i in dendrogram.get("leaves", []) ]
            plv.update({"dendrogram": dendrogram})

    return plv

################################################################################
################################################################################
################################################################################

def _plot_add_samplestrips(plv, byc):

    plv.update( {"plot_first_area_y0": plv["Y"] })
    plv["pls"].append("")
    plv.update( {"plot_strip_bg_i": len(plv["pls"]) - 1 })

    lab_x_e = plv["plot_area_x0"] - plv["plot_region_gap_width"] * 2
    lab_f_s = round(plv["plot_samplestrip_height"] * 0.65, 1)

    if len(plv["results"]) > 0:

        _plot_order_samples(plv, byc)

        plv["styles"].append(
            f'.title-left {{text-anchor: end; fill: { plv["plot_font_color"] }; font-size: { lab_f_s }px;}}'
        )

        for s in plv["results"]:
            _plot_add_one_samplestrip(plv, s, byc)
            if lab_f_s > 5:
                cs_id = s.get("callset_id", "")
                if len(cs_id) > 0:
                    cs_id = f' ({cs_id})'
                g_lab = f'{s.get("biosample_id", "")}{cs_id}'
                plv["pls"].append(f'<text x="{lab_x_e}" y="{ plv["Y"] - round(plv["plot_samplestrip_height"] * 0.2, 1) }" class="title-left">{g_lab}</text>')

    plv["plot_last_histo_ye"] = plv["Y"]

    #----------------------- plot cluster tree --------------------------------#

    plv.update({"cluster_head_gap": 0})
    _plot_add_cluster_tree(plv, plv["plot_samplestrip_height"], byc)

    #--------------------- plot area background -------------------------------#

    x_a_0 = plv["plot_area_x0"]
    p_a_w = plv["plot_area_width"]
    p_a_h = plv["Y"] - plv["plot_first_area_y0"]
    
    plv["pls"][ plv["plot_strip_bg_i"] ] = f'<rect x="{x_a_0}" y="{plv["plot_first_area_y0"]}" width="{p_a_w}" height="{p_a_h}" class="plot-area" />'
    plv["Y"] += plv["plot_region_gap_width"]

    return plv

################################################################################

def _plot_add_cluster_tree(plv, itemHeight, byc):

    d = plv.get("dendrogram", False)

    if d is False:
        return plv

    p_s_c = plv.get("plot_dendrogram_color", '#ee0000')
    p_s_w = plv.get("plot_dendrogram_stroke", 1)

    d_x_s = d.get("dcoord", []) 
    d_y_s = d.get("icoord", []) 

    t_y_0 = plv["plot_first_area_y0"]
    t_x_0 = plv["plot_area_x0"] + plv["plot_area_width"]
    t_y_f = itemHeight * 0.1

    # finding the largest x-value of the dendrogram for scaling
    x_max = plv["plot_dendrogram_width"]

    for i, node in enumerate(d_x_s):
        for j, x in enumerate(node):
            if x > x_max:
                x_max = x
    t_x_f = plv["plot_dendrogram_width"] / x_max

    for i, node in enumerate(d_x_s):

        n = f'<polyline points="'

        for j, x in enumerate(node):
            y = d_y_s[i][j] * t_y_f - plv["cluster_head_gap"]

            for h, f_set in enumerate(plv["results"]):
                h_y_e = h * (itemHeight + plv["cluster_head_gap"])
                if y > h_y_e:
                    y += plv["cluster_head_gap"]

            n += f' { round(t_x_0 + x * t_x_f, 1) },{round(t_y_0 + y, 1)}'

        n += f'" fill="none" stroke="{p_s_c}" stroke-width="{p_s_w}px" />'

        plv["pls"].append(n)

    return plv

################################################################################

def _plot_add_one_samplestrip(plv, s, byc):

    v_s = s.get("variants", [])

    X = plv["plot_area_x0"]
    H = plv["plot_samplestrip_height"]

    cnv_c = {
      "DUP": plv["plot_dup_color"],
      "DEL": plv["plot_del_color"]
    }

    for chro in plv["plot_chros"]:

        c_l = byc["cytolimits"][str(chro)]
        chr_w = c_l["size"] * plv["plot_b2pf"]

        c_v_s = list(filter(lambda d: d[ "reference_name" ] == chro, v_s.copy()))
        c_v_no = len(c_v_s)

        for p_v in c_v_s:
            s_v = int(p_v.get("start", 0))
            e_v = int(p_v.get("end", s_v))
            l_v = round((e_v - s_v)  * plv["plot_b2pf"], 1)
            if l_v < 0.5:
                l_v = 0.5
            v_x = round(X + s_v * plv["plot_b2pf"], 1)
            t = p_v.get("variant_type", "NA")
            c = cnv_c.get(t, "rgb(111,111,111)")

            plv["pls"].append(f'<rect x="{v_x}" y="{plv["Y"]}" width="{l_v}" height="{H}" style="fill: {c} " />')

        X += chr_w
        X += plv["plot_region_gap_width"]

    plv["Y"] += H

    return plv

################################################################################
################################################################################
################################################################################

def _plot_add_one_histogram(plv, f_set, byc):

    _plot_add_one_histogram_canvas(plv, f_set, byc)

    i_f = f_set.get("interval_frequencies", [])

    X = plv["plot_area_x0"]
    h_y_0 = plv["Y"] + plv["plot_area_height"] * 0.5

    #------------------------- histogram data ---------------------------------#

    # TODO: in contrast to the Perl version here we don't correct for interval
    #       sets which _do not_ correspond to the full chromosome coordinates

    cnv_c = {
      "gain_frequency": plv["plot_dup_color"],
      "loss_frequency": plv["plot_del_color"]
    }
    cnv_f = { "gain_frequency": -1, "loss_frequency": 1 }

    for chro in plv["plot_chros"]:

        c_l = byc["cytolimits"][str(chro)]
        chr_w = c_l["size"] * plv["plot_b2pf"]

        c_i_f = list(filter(lambda d: d[ "reference_name" ] == chro, i_f.copy()))
        c_i_no = len(c_i_f)

        for GL in ["gain_frequency", "loss_frequency"]:

            p_c = cnv_c[GL]
            h_f = cnv_f[GL]

            p = f'<polygon points="{ round(X, 1) },{ round(h_y_0, 1) }'

            i_x_0 = X
            prev = -1
            for c_i_i, i_v in enumerate(c_i_f, start=1):

                s = i_x_0 + i_v.get("start", 0) * plv["plot_b2pf"]
                e = i_x_0 + i_v.get("end", 0) * plv["plot_b2pf"]
                v = i_v.get(GL, 0)
                h = v * plv["plot_y2pf"]
                h_p = h_y_0 + h * h_f

                point = f' { round(s, 1) },{round(h_p, 1)}'

                # This construct avoids adding intermediary points w/ the same
                # value as the one before and after 
                if c_i_no > c_i_i:
                    future = c_i_f[c_i_i].get(GL, 0)
                    if prev != v or future != v:
                        p += point
                else:
                    p += point

                prev = v

            p += f' { round((X + chr_w), 1) },{ round(h_y_0, 1) }" fill="{p_c}" stroke-width="0px" />'
            plv["pls"].append(p)

            i_x_0 += i_v.get("start", 0) * plv["plot_b2pf"]

        X += chr_w
        X += plv["plot_region_gap_width"]

    #------------------------ / histogram data --------------------------------#

    plv["Y"] += plv["plot_area_height"]
    plv.update( {"plot_last_histo_ye": plv["Y"] })
    plv["Y"] += plv["plot_region_gap_width"]

    return plv

################################################################################

def _plot_add_one_histogram_canvas(plv, f_set, byc):

    x_a_0 = plv["plot_area_x0"]
    p_a_w = plv["plot_area_width"]
    p_a_h = plv["plot_area_height"]

    #-------------------------- left labels -----------------------------------#
    
    _histoplot_add_left_labels(plv, f_set, byc)

    #--------------------- plot area background -------------------------------#
    
    plv["pls"].append(f'<rect x="{x_a_0}" y="{plv["Y"]}" width="{p_a_w}" height="{p_a_h}" class="plot-area" />')

    #--------------------------- grid lines -----------------------------------#

    _plot_area_add_grid(plv, byc)

    return plv

################################################################################

def _histoplot_add_left_labels(plv, f_set, byc):

    if plv["results_number"] < 2:
        return plv

    lab_x_e = plv["plot_margins"] + plv["plot_labelcol_width"]
    h_y_0 = plv["Y"] + plv["plot_area_height"] * 0.5

    plv["styles"].append(
        f'.title-left {{text-anchor: end; fill: { plv["plot_font_color"] }; font-size: { plv["plot_labelcol_font_size"] }px;}}'
    )
    
    g_id = f_set.get("group_id", "NA")
    g_ds_id = f_set.get("dataset_id", False)
    g_lab = f_set.get("label", "")
    g_no = f_set.get("sample_count", 0)

    # The condition splits the label data on 2 lines if a text label pre-exists
    if len(byc["dataset_ids"]) > 1 and g_ds_id is not False:
        count_lab = f' ({g_ds_id}, {g_no} { "samples" if g_no > 1 else "sample" })'
    else:
        count_lab = f' ({g_no} {"samples" if g_no > 1 else "sample"} )'

    if len(g_lab) > 0:
        lab_y = h_y_0 - plv["plot_labelcol_font_size"] * 0.2
        plv["pls"].append(f'<text x="{lab_x_e}" y="{lab_y}" class="title-left">{g_lab}</text>')
        lab_y = h_y_0 + plv["plot_labelcol_font_size"] * 1.2
        plv["pls"].append(f'<text x="{lab_x_e}" y="{lab_y}" class="title-left">{g_id}{count_lab}</text>')
    else:
        lab_y = h_y_0 - plv["plot_labelcol_font_size"] * 0.5
        plv["pls"].append(f'<text x="{lab_x_e}" y="{lab_y}" class="title-left">{g_id}{count_lab}</text>')

    return plv

################################################################################

def _plot_area_add_grid(plv, byc):

    x_a_0 = plv["plot_area_x0"]
    x_c_e = plv["plot_area_xe"]

    h_y_0 = plv["Y"] + plv["plot_area_height"] * 0.5
    x_y_l = x_a_0 - plv["plot_region_gap_width"]

    plv["styles"].append(
        f'.label-y {{text-anchor: end; fill: { plv["plot_label_y_font_color"] }; font-size: {plv["plot_label_y_font_size"]}px;}}'
    )   
    plv["styles"].append(
        f'.gridline {{stroke-width: {plv["plot_grid_stroke"]}px; stroke: {plv["plot_grid_color"]}; opacity: {plv["plot_grid_opacity"]} ; }}',
    )   

    #-------------------------- center line -----------------------------------#

    plv["pls"].append(f'<line x1="{x_a_0 - plv["plot_region_gap_width"]}"  y1="{h_y_0}"  x2="{x_c_e}"  y2="{h_y_0}" class="gridline" />')

    #--------------------------- grid lines -----------------------------------#

    for y_m in plv["plot_histogram_label_y_values"]:

        if y_m > plv["plot_axis_y_max"]:
            continue

        for f in [1, -1]:

            y_v = h_y_0 + f * y_m * plv["plot_y2pf"]
            y_l_y = y_v + plv["plot_label_y_font_size"] / 2

            plv["pls"].append(f'<line x1="{x_a_0}" y1="{y_v}" x2="{x_c_e}" y2="{y_v}" class="gridline" />')

            if plv["plot_axislab_y_width"] < 1:
                continue

            plv["pls"].append(f'<text x="{x_y_l}" y="{y_l_y}" class="label-y">{y_m}%</text>')

    return plv

################################################################################

def _plot_add_markers(plv, byc):

    _add_labs_from_plot_region_labels(plv, byc)
    _add_labs_from_gene_symbols(plv, byc)
    _add_labs_from_cytobands(plv, byc)

    labs = plv["plot_labels"]

    if not labs:
        return plv

    b2pf = plv["plot_b2pf"]

    p_m_f_s = plv["plot_marker_font_size"]
    p_m_l_p = plv["plot_marker_label_padding"]
    p_m_lane_p = plv["plot_marker_lane_padding"]
    p_m_l_h = p_m_f_s + p_m_l_p * 2
    p_m_lane_h = p_m_l_h + p_m_lane_p

    max_lane = 0
    marker_y_0 = round(plv["plot_first_area_y0"], 1)
    marker_y_e = round(plv["plot_last_histo_ye"] + p_m_lane_p, 1)

    X = plv["plot_area_x0"]

    m_p_e = [ (X - 30) ]
    for chro in plv["plot_chros"]:

        c_l = byc["cytolimits"][str(chro)]
        chr_w = c_l["size"] * plv["plot_b2pf"]

        for m_k, m_v in labs.items():

            c = str(m_v.get("chro", "__na__"))

            if str(chro) != c:
                continue

            s = int(m_v.get("start", 0))
            e = int(m_v.get("end", 0))
            l = m_v.get("label", "")       

            m_s = X + s * b2pf
            m_e = X + e * b2pf
            m_w = m_e - m_s
            if m_w < 1 and m_w > 0:
                m_w = 1
            else:
                m_w = round(m_w, 1)
            m_c = round((m_s + m_e) / 2, 1)
            m_l_w = len(l) * 0.75 * p_m_f_s
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

            plv["pls"].append(f'<rect x="{ round(m_s, 1) }" y="{ marker_y_0 }" width="{ round(m_w, 1) }" height="{ m_h }" class="marker" style="opacity: 0.4; " />')
            plv["pls"].append(f'<rect x="{ round(m_l_s, 1) }" y="{ m_y_e }" width="{ round(m_l_w, 1) }" height="{ p_m_l_h }" class="marker" style="opacity: 0.1; " />')            
            plv["pls"].append(f'<text x="{ m_c }" y="{ l_y_p }" class="marker">{l}</text>')

        X += chr_w
        X += plv["plot_region_gap_width"]

    #--------------------- end chromosome loop --------------------------------#
    
    if max_lane > 0:
        plv["Y"] += max_lane * p_m_lane_h
        plv["Y"] += plv["plot_region_gap_width"]
        plv["styles"].append(
            f'.marker {{text-anchor: middle; fill: { plv["plot_marker_font_color"] }; font-size: { p_m_f_s }px;}}'
        )

    return plv

################################################################################

def _add_labs_from_plot_region_labels(plv, byc):

    r_l_s = plv.get("plot_region_labels", [])
    if len(r_l_s) < 1:
        return plv

    for l in r_l_s:

        l_i = re.split(":", l)
        if len(l_i) < 2:
            continue
        c = l_i.pop(0)
        s_e_i = l_i.pop(0)
        s_e = re.split("-", s_e_i)
        s = s_e.pop(0)
        # TODO: check r'^\d+?$'
        if len(s_e) < 1:
            e = str(int(s)+1)
        else:
            e = s_e.pop(0)
        if len(l_i) > 0:
            label = str(l_i.pop(0))
        else:
            label = ""

        m = _make_marker_object(c, s, e, label)
        plv["plot_labels"].update(m)

    return plv

################################################################################

def _add_labs_from_gene_symbols(plv, byc):

    g_s_s = plv.get("plot_gene_symbols", [])
    if len(g_s_s) < 1:
        return plv

    g_l = []

    for q_g in g_s_s:
        genes, e = retrieve_gene_id_coordinates(q_g, byc)
        g_l += genes

    for f_g in g_l:

        m = _make_marker_object(
            f_g.get("reference_name", False),
            f_g.get("start", False),
            f_g.get("end", False),
            plv.get("plot_marker_font_color", "#ccccff"),
            f_g.get("symbol", False)          
        )

        if m is not False:
            plv["plot_labels"].update(m)

    return plv

################################################################################

def _add_labs_from_cytobands(plv, byc):

    g_s_s = plv.get("plot_cytoregion_labels", [])
    if len(g_s_s) < 1:
        return plv

    g_l = []

    for q_g in g_s_s:
        cytoBands, chro, start, end, error = bands_from_cytobands(q_g, byc)
        if len( cytoBands ) < 1:
            continue

        m = _make_marker_object(
            chro,
            start,
            end,
            plv.get("plot_cytoregion_color", "#ccccff"),
            q_g
        )

        if m is not False:
            plv["plot_labels"].update(m)

    return plv

################################################################################

def _make_marker_object(chromosome, start, end, color, label=""):

    m = False

    # Checks here or upstream?
    if False in [chromosome, start, end, label]:
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

################################################################################

def _plot_add_footer(plv, byc):

    today = datetime.date.today()
    x_a_0 = plv["plot_area_x0"]
    x_c_e = x_a_0 + plv["plot_area_width"]

    plv["styles"].append(
        f'.footer-r {{text-anchor: end; fill: { plv["plot_footer_font_color"] }; font-size: {plv["plot_footer_font_size"]}px;}}'
    )   
    plv["styles"].append(
        f'.footer-l {{text-anchor: start; fill: { plv["plot_footer_font_color"] }; font-size: {plv["plot_footer_font_size"]}px;}}'
    )   

    plv["Y"] += plv["plot_footer_font_size"]
    plv["pls"].append(f'<text x="{x_c_e}" y="{plv["Y"]}" class="footer-r">&#169; CC-BY 2001 - {today.year} progenetix.org</text>')

    if len(plv["results"]) > 1:
        plv["pls"].append(f'<text x="{x_a_0}" y="{plv["Y"]}" class="footer-l">{ len(plv["results"]) } analyses</text>')

    return plv

################################################################################

def _plot_add_cytoband_svg_gradients(plv):

    c_defs = ""

    for cs_k, cs_c in plv["cytoband_shades"].items():

        p_id = plv.get("plot_id", "")
        c_defs += f'\n<linearGradient id="{p_id}{cs_k}" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">'

        for k, v in cs_c.items():
            c_defs += f'\n  <stop offset="{k}" stop-color="{v}" />'

        c_defs += f'\n</linearGradient>'

    plv["pls"].insert(0, c_defs)

    return plv

################################################################################

def _create_svg(plv):

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
        plv["plot_id"],
        plv["plot_width"],
        plv["Y"],
        "\n  ".join(plv["styles"]),
        plv["plot_width"],
        plv["Y"],
        plv["plot_canvas_color"],
        "\n".join(plv["pls"])
    )

    return svg

################################################################################
################################################################################
################################################################################

def bycon_bundle_create_callsets_plot_list(bycon_bundle, byc):

    c_p_l = []
    for p_o in bycon_bundle["callsets"]:
        cs_id = p_o.get("id")
        p_o.update({
            "ds_id": bycon_bundle.get("ds_id", ""),
            "variants":[]
        })

        for v in bycon_bundle["variants"]:
            if v.get("callset_id", "") == cs_id:
                v = de_vrsify_variant(v, byc)
                p_o["variants"].append(v)

        c_p_l.append(p_o)
        
    return c_p_l

################################################################################

def bycon_bundle_create_intervalfrequencies_object(bycon_bundle, byc):

    i_p_o = callsets_create_iset("import", "", bycon_bundle["callsets"], byc)

    return i_p_o

