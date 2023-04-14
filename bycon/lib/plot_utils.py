import re
import datetime
from urllib.parse import unquote

################################################################################

def histoplot_svg_generator(byc, results):

    if not "histoplot" in byc["output"]:
        return byc

    plv = _initialize_plot_values(byc, results)

    _plot_add_title(plv, byc)
    _plot_add_cytobands(plv, byc)
    _plot_add_histodata(plv, results, byc)
    _plot_add_labels(plv, byc)
    _plot_add_footer(plv, results, byc)

    plv["Y"] += plv["plot_margins"]

    #--------------------------------------------------------------------------#

    svg = """
<svg
xmlns="http://www.w3.org/2000/svg"
xmlns:xlink="http://www.w3.org/1999/xlink"
version="1.1"
id="{}"
width="{}px"
height="{}px"
style="margin: auto; font-family: Helvetica, sans-serif;">
<style type="text/css"><![CDATA[
    .title-left {{text-anchor: end; fill: {}; font-size: {}px;}}
    .label-y {{text-anchor: end; fill: {}; font-size: {}px;}}
    .footer-r {{text-anchor: end; fill: {}; font-size: {}px;}}
    .footer-l {{text-anchor: start; fill: {}; font-size: {}px;}}
    .marker {{text-anchor: middle; fill: {}; font-size: {}px;}}
    .cen {{stroke-width: {}px; stroke: {}; opacity: 0.8 ; }}
]]></style>
<rect x="0" y="0" width="{}" height="{}" style="fill: {}" />
{}
</svg>""".format(
        plv["plot_id"],
        plv["plot_width"],
        plv["Y"],
        plv["plot_font_color"],
        plv["plot_font_size"],
        plv["plot_label_y_font_color"],
        plv["plot_label_y_font_size"],
        plv["plot_footer_font_color"],
        plv["plot_footer_font_size"],
        plv["plot_footer_font_color"],
        plv["plot_footer_font_size"],
        plv["plot_marker_font_color"],
        plv["plot_marker_font_size"],
        plv["plot_centerline_stroke"],
        plv["plot_grid_color"],
        plv["plot_width"],
        plv["Y"],
        plv["plot_canvas_color"],
        "\n".join(plv["pls"])
    )

    # print("Content-type: text\n\n")
    print("Content-type: image/svg+xml\n\n")
    print(svg)
    exit()

################################################################################

def _initialize_plot_values(byc, results):

    p_d_p = byc["plot_defaults"]["parameters"]
    r_no = len(results)

    plv = {
        "pls": [],
        "histogram_number": r_no
    }

    for p_k, p_d in p_d_p.items():
        plv.update({ p_k: p_d.get("default", "") })

    if plv["histogram_number"] < 2:
        plv.update({ "plot_labelcol_width": 0 })

    _plot_get_form_parameters(plv, byc)

    pax = plv["plot_margins"] + plv["plot_labelcol_width"] + plv["plot_axislab_y_width"]

    paw = plv["plot_width"] - 2 * plv["plot_margins"]
    paw -= plv["plot_labelcol_width"]
    paw -= plv["plot_axislab_y_width"]
    paw -= plv["plot_treecol_width"]

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
        if plv["histogram_number"] == 1:
            title = _format_resultset_title(results[0])

    plv.update({
        "plot_title": title,
        "Y": plv["plot_margins"],
        "plot_area_width": paw,
        "plot_area_x0": pax,
        "plot_area_xe": pax + paw,
        "plot_area_xc": pax + paw / 2,
        "plot_y2pf": pyf,
        "plot_genome_size": chr_b_s,
        "plot_b2pf": b2pf
    })

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

def _plot_get_form_parameters(plv, byc):

    p_d_p = byc["plot_defaults"]["parameters"]
    p_d_l = byc["plot_defaults"]["legacy_parameters"]
    form = byc["form_data"]

    for p_k, p_d in p_d_p.items():
        if p_k in form:
            plv.update({ p_k: form[p_k]})
        l_p = p_d_l.get(p_k, False)
        if l_p is not False:
            if l_p in byc["form_data"]:
                plv.update({ p_k: form[l_p]})

        if "int" in p_d.get("type", "string"):
            plv.update({ p_k: int(plv[p_k])})
        
        elif "array" in p_d.get("type", "string"):
            if isinstance(plv[p_k], str):
                plv.update({ p_k: unquote(plv[p_k]) })
                plv.update({ p_k: re.split(",", plv[p_k])})
            if "int" in p_d.get("items", "string"):
                plv.update({ p_k: list(map(int, plv[p_k])) })

    return plv

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

            plv["pls"].append(f'<rect x="{X}" y="{by}" width="{l_px}" height="{bh}" style="fill: url(#{plv["plot_id"]}{c}); " />')

            X += l_px

        X += plv["plot_region_gap_width"]

    #-------------------------- / chromosomes ---------------------------------#

    plv["Y"] += plv["plot_chro_height"]
    plv["Y"] += plv["plot_region_gap_width"]

    return plv

################################################################################

def _plot_add_histodata(plv, results, byc):

    plv.update( {"plot_first_histo_y0": plv["Y"] })

    for f_set in results:
        _plot_add_one_histogram(plv, f_set, byc)

    return plv

################################################################################

def _plot_add_one_histogram(plv, f_set, byc):

    _plot_add_histogram_canvas(plv, f_set, byc)

    i_f = f_set.get("interval_frequencies", [])

    X = plv["plot_area_x0"]
    h_y_0 = plv["Y"] + plv["plot_area_height"] * 0.5

    #------------------------- histogram data ---------------------------------#

    # TODO: in contrast to the Perl version here we don't correct for interval
    #       sets which _do not_ correspond to the full chromosome coordinates

    for chro in plv["plot_chros"]:

        c_l = byc["cytolimits"][str(chro)]
        chr_w = c_l["size"] * plv["plot_b2pf"]

        c_i_f = list(filter(lambda d: d[ "reference_name" ] == chro, i_f.copy()))

        for GL in ["gain_frequency", "loss_frequency"]:

            if "gain_frequency" in GL:
                h_f = -1
                p_c = plv["plot_dup_color"]
            else:
                h_f = 1
                p_c = plv["plot_del_color"]

            p = f'<polygon points="\n{ round(X, 1) } { round(h_y_0, 1) }'

            i_x_0 = X
            for i_v in c_i_f:
                s = i_x_0 + i_v.get("start", 0) * plv["plot_b2pf"]
                e = i_x_0 + i_v.get("end", 0) * plv["plot_b2pf"]
                h = i_v.get(GL, 0) * plv["plot_y2pf"]
                h_p = h_y_0 + h * h_f

                p += f'\n{ round(s, 1) } {round(h_p, 1)}'

            p += f'\n{ round((X + chr_w), 1) } { round(h_y_0, 1) }"' 
            p += f'\nfill="{p_c}" stroke-width="0px" />'

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

def _plot_add_histogram_canvas(plv, f_set, byc):

    x_a_0 = plv["plot_area_x0"]
    x_c_e = plv["plot_area_xe"]

    h_y_0 = plv["Y"] + plv["plot_area_height"] * 0.5
    x_y_l = x_a_0 - plv["plot_region_gap_width"]

    p_a_w = plv["plot_area_width"]
    p_a_h = plv["plot_area_height"]
    p_a_c = plv["plot_area_color"]

    #-------------------------- left labels -----------------------------------#

    lab_x_e = plv["plot_margins"] + plv["plot_labelcol_width"]
    lab_y = h_y_0 + plv["plot_labelcol_font_size"] / 2

    if plv["histogram_number"] > 1:
        label = _format_resultset_title(f_set)
        plv["pls"].append(f'<text x="{lab_x_e}" y="{h_y_0}" class="title-left">{label}</text>')

    #--------------------- plot area background -------------------------------#

    plv["pls"].append(f'<rect x="{x_a_0}" y="{plv["Y"]}" width="{p_a_w}" height="{p_a_h}" style="fill: {p_a_c}; fill-opacity: 0.8; " />')

    #-------------------------- center line -----------------------------------#

    plv["pls"].append(f'<line x1="{x_a_0}"  y1="{h_y_0}"  x2="{x_c_e}"  y2="{h_y_0}" class="cen" />')

    #--------------------------- grid lines -----------------------------------#

    for y_m in plv["plot_histogram_frequency_labels"]:

        if y_m > plv["plot_axis_y_max"]:
            continue

        for f in [1, -1]:

            y_v = h_y_0 + f * y_m * plv["plot_y2pf"]
            y_l_y = y_v + plv["plot_label_y_font_size"] / 2

            plv["pls"].append(f'<line x1="{x_a_0}" y1="{y_v}" x2="{x_c_e}" y2="{y_v}" class="cen" />')
            plv["pls"].append(f'<text x="{x_y_l}" y="{y_l_y}" class="label-y">{y_m}%</text>')

    #------------------------- / grid lines -----------------------------------#

    return plv

################################################################################

def _plot_add_labels(plv, byc):

    labs = plv.get("plot_region_labels", [])

    if len(labs) < 1:
        return plv

    b2pf = plv["plot_b2pf"]

    marker_status = False

    for l in labs:

        X = plv["plot_area_x0"]
        m = "marker"

        l_i = re.split(":", l)
        if len(l_i) < 2:
            continue
        l_c = l_i.pop(0)
        s_e_i = l_i.pop(0)
        s_e = re.split("-", s_e_i)
        s = s_e.pop(0)
        # TODO: check r'^\d+?$'
        s = int(s)
        if len(s_e) < 1:
            e = s+1
        else:
            e = s_e.pop(0)
        e = int(e)
        if len(l_i) > 0:
            m = str(l_i.pop(0))

        for chro in plv["plot_chros"]:

            c_l = byc["cytolimits"][str(chro)]
            chr_w = c_l["size"] * plv["plot_b2pf"]

            if str(l_c) == str(chro):
                m_s = X + s * b2pf
                m_e = X + e * b2pf
                # print(f"{s} => {e}")
                m_w = (e - s) * b2pf
                if m_w < 1:
                    m_w = 1
                m_c = round((m_s + m_e) / 2, 1)
                m_y_0 = plv["plot_first_histo_y0"] - 1
                m_y_e = plv["plot_last_histo_ye"] + 1
                l_y = plv["plot_last_histo_ye"] + plv["plot_footer_font_size"]
                m_h = round(m_y_e - m_y_0, 1)

                # print(f'<rect x="{m_s}" y="{m_y_0}" width="{m_w}" height="{m_h}" style="fill: #66ddff; opacity: 0.4; " />')

                plv["pls"].append(f'<rect x="{ round(m_s, 1)}" y="{ round(m_y_0, 1)}" width="{ round(m_w, 1) }" height="{ round(m_h, 1) }" class="marker" style="opacity: 0.4; " />')
                plv["pls"].append(f'<text x="{m_c}" y="{l_y}" class="marker">{m}</text>')
                marker_status = True

            X += chr_w
            X += plv["plot_region_gap_width"]
        
        if marker_status is True:
            plv["Y"] += plv["plot_footer_font_size"]

    return plv

################################################################################


def _plot_add_footer(plv, results, byc):

    today = datetime.date.today()
    x_a_0 = plv["plot_area_x0"]
    x_c_e = x_a_0 + plv["plot_area_width"]

    plv["Y"] += plv["plot_footer_font_size"]
    plv["pls"].append(f'<text x="{x_c_e}" y="{plv["Y"]}" class="footer-r">&#169; CC-BY 2001 - {today.year} progenetix.org</text>')

    if plv["histogram_number"] == 1:
        s_no = results[0].get("sample_count", "?")
        plv["pls"].append(f'<text x="{x_a_0}" y="{plv["Y"]}" class="footer-l">{s_no} samples</text>')

    return plv

################################################################################

def _plot_add_cytoband_svg_gradients(plv):

    plv["pls"].insert(0, 
"""
<linearGradient id="{0}gpos100" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">
    <stop offset="0%" stop-color="rgb(39,39,39)" />
    <stop offset="100%" stop-color="rgb(0,0,0)" />
</linearGradient>
<linearGradient id="{0}gpos75" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">
    <stop offset="0%" stop-color="rgb(87,87,87)" />
    <stop offset="100%" stop-color="rgb(39,39,39)" />
</linearGradient>
<linearGradient id="{0}gpos50" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">
    <stop offset="0%" stop-color="rgb(196,196,196)" />
    <stop offset="100%" stop-color="rgb(111,111,111)" />
</linearGradient>
<linearGradient id="{0}gpos25" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">
    <stop offset="0%" stop-color="rgb(223,223,223)" />
    <stop offset="100%" stop-color="rgb(196,196,196)" />
</linearGradient>
<linearGradient id="{0}gneg" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">
    <stop offset="0%" stop-color="white" />
    <stop offset="100%" stop-color="rgb(223,223,223)" />
</linearGradient>
<linearGradient id="{0}gvar" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">
    <stop offset="0%" stop-color="rgb(196,196,196)" />
    <stop offset="100%" stop-color="rgb(111,111,111)" />
</linearGradient>
<linearGradient id="{0}stalk" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">
    <stop offset="0%" stop-color="rgb(39,39,39)" />
    <stop offset="100%" stop-color="rgb(0,0,0)" />
</linearGradient>
<linearGradient id="{0}acen" x1="0%" x2="0%" y1="0%" y2="80%" spreadMethod="reflect">
    <stop offset="0%" stop-color="rgb(163,55,247)" />
    <stop offset="100%" stop-color="rgb(138,43,226)" />
</linearGradient>
""".format(plv["plot_id"])
    )

    return plv

