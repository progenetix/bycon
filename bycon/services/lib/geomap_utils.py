import math, re, sys
from os import path
from humps import decamelize

from bycon import BYC, BYC_PARS, prdbug, test_truthy

services_lib_path = path.join( path.dirname( path.abspath(__file__) ) )
sys.path.append( services_lib_path )
from beacon_response_generation import print_html_response
from bycon_plot import ByconPlotPars
from file_utils import read_www_tsv_to_dictlist

################################################################################

def read_geomarker_table_web():
    geolocs = []
    f_a = BYC_PARS.get("inputfile", "")
    if not "http" in f_a:
        return geolocs
    lf, fieldnames = read_www_tsv_to_dictlist(f_a)

    markers = {}
    for line in lf:
        group_lon = line.get("group_lon", "")       # could use 0 here for Null Island...
        group_lat = line.get("group_lat", "")       # could use 0 here for Null Island...
        group_label = line.get("group_label", "")
        item_size = line.get("item_size", "")
        item_label = line.get("item_label", "")
        item_link = line.get("item_link", "")

        if not re.match(r'^\-?\d+?(?:\.\d+?)?$', str(group_lat) ):
            continue
        if not re.match(r'^\-?\d+?(?:\.\d+?)?$', str(group_lon) ):
            continue
        if not re.match(r'^\d+?(?:\.\d+?)?$', str(item_size) ):
            item_size = 1

        m_k = f'{group_label}::LatLon::{group_lat}::{group_lon}'

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
                        "marker_type": line.get("marker_type", "circle"),
                        "marker_icon": line.get("marker_icon", ""),
                        "marker_count": 0,
                        "items": []
                    }
                }
            }

        g_l_p = markers[m_k]["geo_location"]["properties"]
        g_l_p["marker_count"] += float(item_size)

        if len(item_label) > 0:
            if "http" in item_link:
                item_label = "<a href='{}' target='_blank'>{}</a>".format(item_link, item_label)
            g_l_p["items"].append(item_label)

    for m_k, m_v in markers.items():
        geolocs.append(m_v)

    return geolocs

################################################################################

class ByconMap:
    """
    TBD
    """

    def __init__(self, geolocs=[]):
        bpp = ByconPlotPars()
        self.plot_type = "geomapplot"
        self.plv = bpp.plotParameters()

        self.map_html = ""
        self.map_script = ""
        self.geolocs = [x["geo_location"] for x in geolocs if "geo_location" in x]
        self.marker_max = 1
        self.leaf_markers = []
        self.markersJS = ""
        self.geoMap = ""
        self.__marker_max_from_geo_locations()        


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def mapHTML(self):
        self.__create_map_html_from_geolocations()
        return self.map_html

    # -------------------------------------------------------------------------#

    def printMapHTML(self):
        self.__create_map_html_from_geolocations()
        print_html_response(self.map_html)
        exit()

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __create_map_html_from_geolocations(self):
        m_p = self.plv
        for geoloc in self.geolocs:
            self.leaf_markers.append( self.__map_marker_from_geo_location(geoloc) )
        self.__create_geo__marker_layer()

        self.geoMap = """
    <!-- map needs to exist before we load leaflet -->
    {}
    <div id="map-canvas" style="width: {}px; height: {}px;"></div>

    <!-- Make sure you put this AFTER Leaflet's CSS -->
    <script src="https://unpkg.com/leaflet@1.8.0/dist/leaflet.js"
          integrity="sha512-BB3hKbKWOc9Ez/TAwyWxNXeoV9c1v6FIeYiBieIWkpLjauysF18NzgR1MBNBXf8/KABdlkX68nAhlwcDFLGPCQ=="
          crossorigin=""></script>
    <script>
      var circleOptions = {{
        color: '{}',
        stroke: true,
        weight: {},
        fillColor: '{}',
        fillOpacity: {},
        radius: 1000,
        count: 1
      }};

      // Create the map.

      var map = L.map('map-canvas', {{ renderer: L.svg() }} ).setView([{}, {}], {});

      L.tileLayer('{}', {{
          minZoom: {},
          maxZoom: {},
          attribution: '{}'
      }}).addTo(map);

    {}

    </script>
        """.format(
            m_p.get("head"),
            m_p.get("map_w_px"),
            m_p.get("map_h_px"),
            m_p.get("bubble_stroke_color"),
            m_p.get("bubble_stroke_weight"),
            m_p.get("bubble_fill_color"),
            m_p.get("bubble_opacity"),
            m_p.get("init_latitude"),
            m_p.get("init_longitude"),
            m_p.get("zoom", 1),
            m_p.get("tiles_source"),
            m_p.get("zoom_min"),
            m_p.get("zoom_max"),
            m_p.get("attribution"),
            self.markersJS
        )

        self.map_html = """
<html>
{}
</html>""".format(self.geoMap)


    # -------------------------------------------------------------------------#

    def __create_geo__marker_layer(self):
        if len(self.leaf_markers) > 0:
            self.markersJS = """
      var markers = [
    {}
      ];
      var markersGroup = L.featureGroup(markers);
      map.addLayer(markersGroup);
      map.fitBounds(markersGroup.getBounds().pad(0.05));
    """.format(",\n".join(self.leaf_markers))


    # -------------------------------------------------------------------------#

    def __marker_max_from_geo_locations(self):
        for g_l in self.geolocs:
            c = float( g_l["properties"].get("marker_count", 1) )
            if c > self.marker_max:
                self.marker_max = c

    # -------------------------------------------------------------------------#

    def __map_marker_from_geo_location(self, geoloc):
        p = geoloc.get("properties", {})
        g = geoloc.get("geometry", {})
        m_t = self.plv.get("marker_type", "marker")
        m_max_r = self.plv.get("marker_max_r", 1000)
        m_f = int(int(m_max_r) / math.sqrt(4 * self.marker_max / math.pi))

        label = p.get("label", None)
        if label is None:
            label = p.get("city", "NA")
            country = p.get("country", None)
            if country:
                label = f'{label}, {country}'

        items = p.get("items", [])
        items = [x for x in items if x is not None]
        if len(items) > 0:
            label += "<hr/>{}".format("<br/>".join(items))
        else:
            label += f'<hr/>latitude: {g["coordinates"][1]}, longitude: {g["coordinates"][0]}'

        count = float(p.get("marker_count", 1))
        size = count * m_f * float(self.plv.get("marker_scale", 2))
        marker_icon = p.get("marker_icon", "")

        if ".png" in marker_icon or ".jpg" in marker_icon:
            m_t = "marker"
        
        if "circle" in m_t:
            map_marker = """
L.{}([{}, {}], {{
    ...circleOptions,
    ...{{radius: {}, count: {}}}
}}).bindPopup("{}", {{maxHeight: 200}})
""".format(
        m_t,
        g["coordinates"][1],
        g["coordinates"][0],
        size,
        count,
        label
    )

        else:
            map_marker = """
L.{}([{}, {}], {{
    ...{{count: {}}}
}}).bindPopup("{}", {{maxHeight: 200}})
""".format(
        m_t,
        g["coordinates"][1],
        g["coordinates"][0],
        count,
        label
    )

        return map_marker


##### LINT #####

#     if test_truthy(BYC_PARS.get("show_help", False)):
#         t = """
# <h4>Map Configuration</h4>
# <p>The following parameters may be modified by providing alternative values in
# the `plotPars` parameter in the URL, e.g. "&plotPars=map_w_px=1024::init_latitude=8.4".

# For information about the special parameter format please see http://byconaut.progenetix.org
# </p>
# <table>
# """
# t += "<tr><th>Map Parameter</th><th>Value</th></tr>\n"
# for p_p_k, p_p_v in p_p.items():
#     if not '<' in str(p_p_v):
#         t += f'<tr><td>{p_p_k}</td><td>{p_p_v}</td></tr>\n'
# t += "\n</table>"
# geoMap += t
