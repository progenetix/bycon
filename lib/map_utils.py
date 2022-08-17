def print_map_from_geolocations(byc, results):

    if not "map" in byc["output"]:
        return

    leaf_markers = []

    m_p = byc["geoloc_definitions"].get("map_params", {})
    radius = 1000
    count = 1

    for g_l in results:

        p = g_l["geo_location"]["properties"]
        g = g_l["geo_location"]["geometry"]
        i = g_l["geo_location"].get("info", {})

        label = i.get("label", None)
        if label is None:
            label = p.get("city", "NA")
            country = p.get("country", None)
            if country is not None:
                label += ", "+country
            label += "<hr/>latitude: {}<br/>longitude: {}".format(g["coordinates"][1], g["coordinates"][0])

        marker = p.get("marker", "marker")

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
            radius,
            count,
            label
        )

        leaf_markers.append(map_marker)


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