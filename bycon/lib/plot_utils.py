import re

################################################################################

def histoplot_svg_generator(byc, results):

    if not "histoplot" in byc["output"]:
        return byc

    plv = _initialize_plot_values(byc)

    _plot_add_title(plv, byc)
    _plot_add_cytobands(plv, byc)
    _plot_add_histodata(plv, results, byc)

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
    .title-left {{text-anchor: middle; fill: {}; font-size: {}px;}}
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

def _initialize_plot_values(byc):

    plv = {
        "pls": []
    }

    for p_k, p_d in byc["plot_defaults"]["parameters"].items():
        plv.update({ p_k: p_d.get("default", "") })
        if p_k in byc["form_data"]:
            plv.update({ p_k: byc["form_data"][p_k]})
        l_p = byc["plot_defaults"]["legacy_parameters"].get(p_k, False)
        if l_p is not False:
            if l_p in byc["form_data"]:
                plv.update({ p_k: byc["form_data"][l_p]})

        if "int" in p_d.get("type", "string"):
            plv.update({ p_k: int(plv[p_k])})
        
        elif "array" in p_d.get("type", "string"):
            if isinstance(plv[p_k], str):
                plv.update({ p_k: re.split(",", plv[p_k])})

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

    pyf = pax * 0.5 / plv["plot_axis_y_max"]

    gaps = len(plv["plot_chros"]) - 1
    gap_sw = gaps * plv["plot_region_gap_width"]
    genome_width = paw - gap_sw
    b2pf = genome_width / chr_b_s # TODO: only exists if using stack

    plv.update({
        "Y": plv["plot_margins"],
        "plot_area_width": paw,
        "plot_area_x0": pax,
        "plot_area_xc": pax + paw / 2,
        "plot_y2pf": pyf,
        "plot_genome_size": chr_b_s,
        "plot_b2pf": b2pf
    })

    return plv

################################################################################

def _plot_add_title(plv, byc):

    if len(plv.get("plot_title", "")) > 0:

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

        plv["pls"].append(
'<text x="{}" y="{}" style="text-anchor: middle; font-size: {}px">{}</text>'.format(
                chr_c,
                plv["Y"],
                plv["plot_font_size"],
                chro
            )
        )

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

            plv["pls"].append(
'<rect x="{}" y="{}" width="{}" height="{}" style="fill: url(#{}{}); " />'.format(
                    X,
                    by,
                    l_px,
                    bh,
                    plv["plot_id"],
                    c
                )
            )

            X += l_px

        X += plv["plot_region_gap_width"]

    #-------------------------- / chromosomes ---------------------------------#

    plv["Y"] += plv["plot_chro_height"]
    plv["Y"] += plv["plot_region_gap_width"]

    return plv

################################################################################

def _plot_add_histodata(plv, results, byc):

    for f_set in results:
        _plot_add_one_histogram(plv, f_set, byc)

    return plv

################################################################################

def _plot_add_one_histogram(plv, f_set, byc):

    _plot_add_histogram_canvas(plv, byc)

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

            p = """<polygon points="
  {} {}""".format(X, h_y_0)

            i_x_0 = X
            for i_v in c_i_f:
                s = i_x_0 + i_v.get("start", 0) * plv["plot_b2pf"]
                e = i_x_0 + i_v.get("end", 0) * plv["plot_b2pf"]
                h = i_v.get(GL, 0) * plv["plot_y2pf"] * 2
                h_p = h_y_0 + h * h_f
                p += """
  {} {}""".format(round(s, 1), round(h_p, 1))

            p += """
  {} {}"
  fill="{}"
  stroke-width="0px"
/>""".format(round((X + chr_w), 1), round(h_y_0, 1), p_c)

            plv["pls"].append(p)

            i_x_0 += i_v.get("start", 0) * plv["plot_b2pf"]

        X += chr_w
        X += plv["plot_region_gap_width"]

    #------------------------ / histogram data --------------------------------#

    plv["Y"] += plv["plot_area_height"]
    plv["Y"] += plv["plot_region_gap_width"]

    return plv

################################################################################

def _plot_add_histogram_canvas(plv, byc):

    plv["pls"].append(
'<rect x="{}" y="{}" width="{}" height="{}" style="fill: {}; fill-opacity: 0.8; " />'.format(
            plv["plot_area_x0"],
            plv["Y"],
            plv["plot_area_width"],
            plv["plot_area_height"],
            plv["plot_area_color"]
        )
    )

    h_y_0 = plv["Y"] + plv["plot_area_height"] * 0.5
    x_c_e = plv["plot_area_x0"] + plv["plot_area_width"]
    plv["pls"].append(
'<line x1="{}"  y1="{}"  x2="{}"  y2="{}" class="cen"  />'.format(
            plv["plot_area_x0"],
            h_y_0,
            x_c_e,
            h_y_0
        )
    )

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

