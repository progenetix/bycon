import math, re, sys
from os import path

from bycon import BYC, BYC_PARS, RefactoredValues, prdbug, print_html_response

services_lib_path = path.join( path.dirname( path.abspath(__file__) ) )
sys.path.append( services_lib_path )
from bycon_plot import ByconPlotPars
from file_utils import ByconTSVreader


class ByconGeolocs:
    def __init__(self, geo_root="geo_location"):
        self.geo_root = geo_root
        self.geo_locations = []
        self.geo_webfile = BYC_PARS.get("inputfile", "")


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_locations_from_web(self):
        self.__read_geomarker_table_web()
        return self.geo_locations


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __read_geomarker_table_web(self):
        if not "http" in self.geo_webfile:
            return

        prdbug(self.geo_webfile)
        lf, fieldnames = ByconTSVreader().www_to_dictlist(self.geo_webfile)

        p_defs = {
            "group_lon": {"type": "number"},
            "group_lat": {"type": "number"},
            "group_label": {"type": "string"},
            "item_size": {"type": "number", "default": 1},
            "item_label": {"type": "string"},
            "item_link": {"type": "string"},
            "marker_type": {"type": "string"},
            "marker_icon": {"type": "string"}
        }
        
        markers = {}
        for line in lf:
            p_vals = {}
            for p in p_defs:
                par_defs = p_defs[p]
                default = par_defs.get("default", "")
                v_s = line.get(p, default)
                prdbug(p)
                prdbug(par_defs)
                prdbug(v_s)

                p_vals.update({p: RefactoredValues(par_defs).refVal(v_s)})

            if not re.match(r'^\-?\d+?(?:\.\d+?)?$', str(p_vals.get("group_lat"))):
                continue
            if not re.match(r'^\-?\d+?(?:\.\d+?)?$', str(p_vals.get("group_lon"))):
                continue
            if not re.match(r'^\d+?(?:\.\d+?)?$', str(p_vals["item_size"])):
                p_vals["item_size"] = 1

            m_k = f'{p_vals["group_label"]}::LatLon::{p_vals["group_lat"]}::{p_vals["group_lon"]}'

            # TODO: load schema for this
            if not m_k in markers.keys():
                markers[m_k] = {
                    "geo_location": {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [ p_vals["group_lon"], p_vals["group_lat"] ]
                        },
                        "properties": {
                            "city": None,
                            "country": None,
                            "label": f'{p_vals["group_label"]}',
                            "marker_type": p_vals["marker_type"],
                            "marker_icon": p_vals["marker_icon"],
                            "marker_count": 0,
                            "items": []
                        }
                    }
                }

            g_l_p = markers[m_k]["geo_location"]["properties"]
            g_l_p["marker_count"] += p_vals["item_size"]

            if p_vals["item_label"] and len(p_vals["item_label"]) > 0:
                if "http" in str(p_vals["item_link"]):
                    p_vals["item_label"] = f'<a href="{p_vals["item_link"]}" target="_blank">{p_vals["item_label"]}</a>'
                g_l_p["items"].append(p_vals["item_label"])

        for m_k, m_v in markers.items():
            self.geo_locations.append(m_v)


################################################################################

class ByconMap:
    def __init__(self):
        bpp = ByconPlotPars()
        self.plot_type = "geomapplot"
        self.plv = bpp.plotParameters()

        self.map_html = ""
        self.map_script = ""
        self.geolocs = []
        self.marker_max = 1
        self.leaf_markers = []
        self.markersJS = ""
        self.geoMap = ""


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def mapHTML(self):
        self.__create_map_html_from_geolocations()
        return self.map_html


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def printMapHTML(self):
        self.__create_map_html_from_geolocations()
        print_html_response(self.map_html)
        exit()


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def add_data_from_results_list(self, geolocs=[]):
        self.geolocs = [x["geo_location"] for x in geolocs if "geo_location" in x]


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def add_data_from_datasets(self, flattened_data=[]):
        self.__geo_bundle_from_datasets_data(flattened_data)


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __create_map_html_from_geolocations(self):
        m_p = self.plv
        self.__marker_max_from_geo_locations()        
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
    # -------------------------------------------------------------------------#

    def __marker_max_from_geo_locations(self):
        for g_l in self.geolocs:
            c = float( g_l["properties"].get("marker_count", 1) )
            if c > self.marker_max:
                self.marker_max = c


    # -------------------------------------------------------------------------#
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
            label += f'<hr/>{"<br/>".join(items)}'
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
}}).bindPopup('{}', {{maxHeight: 200}})
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
}}).bindPopup('{}', {{maxHeight: 200}})
""".format(
        m_t,
        g["coordinates"][1],
        g["coordinates"][0],
        count,
        label
    )

        return map_marker


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __geo_bundle_from_datasets_data(self, flattened_data):
        geokb = {}
        for r in flattened_data:
            try:
                geom = r["geo_location"]["geometry"]
                properties = r["geo_location"]["properties"]
            except:
                continue
            longlat = geom.get("coordinates", [0,0])
            k = f"longlat_{longlat[0]}_{longlat[1]}"
            if k not in geokb:
                geokb.update({k: {
                    "pubmeds": {},
                    "geometry": geom,
                    "properties": properties
                }})
                geokb[k]["properties"].update({"marker_count": 1})
            else:
                geokb[k]["properties"]["marker_count"] += 1

            try:
                pmid = r["references"]["pubmed"]["id"]
                pmid = pmid.replace("pubmed:", "")
                if pmid in geokb[k]["pubmeds"]:
                    geokb[k]["pubmeds"][pmid]["count"] += 1
                else:
                    lab = f'<a href="https://europepmc.org/article/MED/{pmid}"" />{pmid}</a>'
                    geokb[k]["pubmeds"].update({
                        pmid: {
                            "label": lab,
                            "count": 1
                        }
                    })
            except:
                pass

        for k, v in geokb.items():
            m_c = v["properties"].get("marker_count", 0)
            m_l = v["properties"].get("label", "")
            v["properties"].update({
                "label": f'{m_l} ({m_c} {"sample" if m_c == 1 else "samples"})',
                "items": []

            })
            for p_i in v["pubmeds"].values():
                l = p_i.get("label")
                c = p_i.get("count")
                if not l or not c:
                    continue
                # v["geo_location"]["properties"]["items"].append('x')
                v["properties"]["items"].append(f'{l} ({c} {"sample" if c == 1 else "samples"})')

        self.geolocs = geokb.values()

