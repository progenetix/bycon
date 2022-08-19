import math, re, requests
from cgi_parsing import *

################################################################################

def read_geomarker_table_web(byc):

    geolocs = []

    if not "http" in byc["form_data"]["file"]:
        return geolocs

    lf = re.split("\n", requests.get(byc["form_data"]["file"]).text)

    markers = {}

    for line in lf:

        if line.startswith('#'):
            continue

        line += "\t\t\t\t"
        l_l = line.split("\t")
        if len(l_l) < 6:
            continue
        group_label, group_lat, group_lon, item_size, item_label, item_link, markerType, *_ = l_l[:7]

        if not re.match(r'^\-?\d+?(?:\.\d+?)?$', group_lat):
            continue
        if not re.match(r'^\-?\d+?(?:\.\d+?)?$', group_lon):
            continue
        if not re.match(r'^\d+?(?:\.\d+?)?$', item_size):
            item_size = 1

        m_k = "{}::{}::{}".format(group_label, group_lat, group_lon)
        if markerType not in ["circle", "marker"]:
            markerType = "circle"

        # TODO: load schema for this
        if not m_k in markers.keys():
            markers[m_k] = {
                "geo_location": {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [ float(group_lon), float(group_lat) ]
                    },
                    "properties": {
                        "city": None,
                        "country": None,
                        "label": group_label,
                        "marker_type": markerType,
                        "marker_count": 0,
                        "items": []
                    }
                }
            }

        g_l_p = markers[m_k]["geo_location"]["properties"]
        g_l_p["marker_count"] += float(item_size)

        if len(item_label) > 0:
            if "http" in item_link:
                item_label = "<a href='{}'>{}</a>".format(item_link, item_label)
            g_l_p["items"].append(item_label)

    for m_k, m_v in markers.items():
        geolocs.append(m_v)

    return geolocs

################################################################################

def print_map_from_geolocations(byc, geolocs):

    if not "map" in byc["output"]:
        return

    m_p = update_map_params_from_form(byc)
    m_max_count = marker_max_from_geo_locations(geolocs)
    
    leaf_markers = []

    for geoloc in geolocs:
        leaf_markers.append( map_marker_from_geo_location(byc, geoloc, m_p, m_max_count) )

    geoMap = """
{}
<!-- map needs to exist before we load leaflet -->
<div id="map-canvas" style="width: {}px; height: {}px;"></div>

<!-- Make sure you put this AFTER Leaflet's CSS -->
<script src="https://unpkg.com/leaflet@1.8.0/dist/leaflet.js"
      integrity="sha512-BB3hKbKWOc9Ez/TAwyWxNXeoV9c1v6FIeYiBieIWkpLjauysF18NzgR1MBNBXf8/KABdlkX68nAhlwcDFLGPCQ=="
      crossorigin=""></script>
<script>
  var markers = [
{}
  ];
  var markersGroup = L.featureGroup(markers);

  // Create the map.

  var map = L.map('map-canvas', {{ renderer: L.svg() }} ).setView([{}, {}], {});

  L.tileLayer('{}', {{
      minZoom: {},
      maxZoom: {},
      attribution: '{}'
  }}).addTo(map);

  map.addLayer(markersGroup);
  map.fitBounds(markersGroup.getBounds().pad(0.05));

</script>
    """.format(
        m_p.get("head"),
        m_p.get("canvas_w_px"),
        m_p.get("canvas_h_px"),
        ",\n".join(leaf_markers),
        m_p.get("latitude"),
        m_p.get("longitude"),
        m_p.get("zoom"),
        m_p.get("tiles_source"),
        m_p.get("zoom_min"),
        m_p.get("zoom_max"),
        m_p.get("attribution")
    )


    if test_truthy(byc["form_data"]["help"]):
        t = """
<h4>Map Configuration</h4>
<p>The following parameters may be modified by providing alternative values in
the URL, e.g. "&canvas_w_px=1024".</p>
<table>
"""
        t += "<tr><th>Map Parameter</th><th>Value</th></tr>\n"
        for m_p_k, m_p_v in m_p.items():
            if not '<' in str(m_p_v):
                t += "<tr><td>{}</td><td>{}</td></tr>\n".format(m_p_k, m_p_v)
        t += "\n</table>"
        geoMap += t
    # except:
    #     pass

    print("""
<html>
{}
</html>""".format(geoMap))

    exit()

################################################################################

def update_map_params_from_form(byc):

    m_p = byc["geoloc_definitions"].get("map_params", {})

    for m_p_k, m_p_v in m_p.items():

        if m_p_k in byc["form_data"]:
            m_p.update({m_p_k: byc["form_data"].get(m_p_k, m_p_v)})

    return m_p

################################################################################

def marker_max_from_geo_locations(geolocs):

    m_max_count = 1
    for g_l in geolocs:
        c = float( g_l["geo_location"]["properties"].get("marker_count", 1) )
        if c > m_max_count:
            m_max_count = c

    return m_max_count

################################################################################

def map_marker_from_geo_location(byc, geoloc, m_p, m_max_count):

    p = geoloc["geo_location"]["properties"]
    g = geoloc["geo_location"]["geometry"]

    marker = p.get("marker_type", "circle")
    if m_max_count == 1:
        marker = "marker"

    m_max_r = m_p.get("marker_max_r", "1000")
    m_f = int(m_max_r / math.sqrt(4 * m_max_count / math.pi))

    label = p.get("label", None)
    if label is None:
        label = p.get("city", "NA")
        country = p.get("country", None)
        if country is not None:
            label = "{}, {}".format(label, country)
        label += "<hr/>latitude: {}<br/>longitude: {}".format(g["coordinates"][1], g["coordinates"][0])
    else:
        items = p.get("items", [])
        if len(items) > 0:
            label = "{}<hr/>{}".format(label, "<br/>".join(items))


    count = float(p.get("marker_count", 1))
    size = count * m_f * float(m_p.get("marker_scale", 2))

    map_marker = """
L.{}([{}, {}], {{
    color: '{}',
    stroke: true,
    weight: {},
    fillColor: '{}',
    fillOpacity: {},
    radius: {},
    count: {}
}}).bindPopup("{}")
    """.format(
        marker,
        g["coordinates"][1],
        g["coordinates"][0],
        m_p["bubble_stroke_color"],
        m_p["bubble_stroke_weight"],
        m_p["bubble_fill_color"],
        m_p["bubble_opacity"],
        size,
        count,
        label
    )

    return map_marker
