import math

def print_map_from_geolocations(byc, results):

    if not "map" in byc["output"]:
        return

    m_p = byc["geoloc_definitions"].get("map_params", {})
    m_max_count = marker_max_from_geo_locations(results)
    
    leaf_markers = []

    for geoloc in results:
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
  // Create the map.
  var map = L.map('map-canvas', {{ renderer: L.svg() }} ).setView([{}, {}], {});

  L.tileLayer('{}', {{
      minZoom: {},
      maxZoom: {},
      {}
      attribution: '{}'
  }}).addTo(map);

{}

</script>
    """.format(
        m_p.get("head"),
        m_p.get("canvas_w_px"),
        m_p.get("canvas_h_px"),
        m_p.get("latitude"),
        m_p.get("longitude"),
        m_p.get("zoom"),
        m_p.get("tiles_source"),
        m_p.get("zoom_min"),
        m_p.get("zoom_max"),
        m_p.get("extra_JS"),
        m_p.get("attribution"),
        ";\n".join(leaf_markers)
    )

    print("""
<html>
{}
</html>""".format(geoMap))

    exit()

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
    size = count * m_f

    map_marker = """
L.{}([{}, {}], {{
    color: '{}',
    stroke: true,
    weight: {},
    fillColor: '{}',
    fillOpacity: {},
    radius: {},
    count: {}
}}).bindPopup("{}").addTo(map)
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
