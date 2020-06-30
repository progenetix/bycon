from os import path
from pymongo import MongoClient
import math
import plotly
import plotly.graph_objects as go
import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html


################################################################################

def plot_sample_geomap( **kwargs ):

    plotly.io.orca.config.executable = "/usr/local/bin/orca"
    args = kwargs[ "args" ]
    label = ""
    if args.label:
        label = args.label

    query = { "_id": { "$in": kwargs["query_results"][ "bs._id" ][ "target_values" ] } }
    ds_id = kwargs["query_results"][ "bs._id" ][ "source_db" ]

    bios_coll = MongoClient( )[ ds_id ][ "biosamples" ]

    mapplot = path.join( kwargs[ "config" ][ "paths" ][ "out" ], "-".join([ ds_id, label, "map.svg" ]) )
    country_data = path.join( kwargs[ "config" ][ "paths" ][ "out" ], "-".join([ ds_id, label, "mapdata.tsv" ]) )    
    city_data = path.join( kwargs[ "config" ][ "paths" ][ "out" ], "-".join([ ds_id, label, "mapdata_city.tsv" ]) )    

    geo_s = [ ]
    for bios in bios_coll.find(query):
        if "provenance" in bios:
            if "geo" in bios[ "provenance" ]:
                geo_s.append(bios["provenance"]["geo"])

    country_counts = _aggregate_country_counts(geo_s)
    all_samples = len( kwargs["query_results"][ "bs._id" ][ "target_values" ] )
    map_samples = sum( country_counts["count"] )
    map_countries = len( country_counts["country"] )

    city_counts = _aggregate_city_counts(geo_s)
    map_cities = len( city_counts["city"] ) 

    df = pd.DataFrame(data=country_counts)
    df.to_csv(country_data, sep='\t', index=False)

    fig = go.Figure()

    fig.add_trace(go.Choropleth(
        locations = df['ISO-3166-alpha3'],
        locationmode = "ISO-3",
        z = df['count'],
        text = df['country'],
        colorscale = 'Blues',
        autocolorscale=False,
        reversescale=False,
        marker_line_color='darkgray',
        marker_line_width=0.5,
        colorbar_tickprefix = '-',
        colorbar_title = 'Samples<br>per country'
        ))

    df = pd.DataFrame(data=city_counts)
    df.to_csv(city_data, sep='\t', index=False)

    fig.add_trace(go.Scattergeo(
        lat=df['latitude'],
        lon=df['longitude'],
        mode='markers',
        marker=go.scattergeo.Marker(
            size=[ math.ceil( math.sqrt( x * 4 / math.pi ) ) for x in df['count']]
        ),
        text=city_counts['label'],
    ))

    fig.update_layout( title_text=("{} Mapped <i><b>{}</b></i> Samples, from {} Cities in {} Countries").format(map_samples, ds_id, map_cities, map_countries) )
    fig.update_geos( landcolor = 'rgb(255,252,225)' )
    fig.update_geos( fitbounds="locations" )

    app = dash.Dash()
    app.layout = html.Div([
        dcc.Graph(figure=fig)
    ])

    app.run_server(debug=True, use_reloader=False)


    # fig.show()

    try:
        fig.write_image(mapplot)
        print('\nGEO map was written in', mapplot, end = '.\n')
    except Exception as e:
        print(e)


################################################################################

def _aggregate_city_counts(geo_s):

    cs = {  }
    for g in geo_s:
        if "city" in g:
            g_k = "{}::{}::{}".format( g["city"], round(g["latitude"],0), round(g["longitude"],0) )
            if g_k in cs:
                cs[ g_k ][ "count" ] += 1
            else:
                cs[ g_k ] = {
                    "count": 1,
                    "city": g["city"],
                    "country": g["country"],
                    "label": g["label"],
                    "latitude": g["latitude"],
                    "longitude": g["longitude"],
                    "ISO-3166-alpha3": g[ "ISO-3166-alpha3" ]
                }

    cs_counts = { "city": [ ], "country": [ ], "label": [ ], "latitude": [ ], "longitude": [ ], "count": [ ], "ISO-3166-alpha3": [ ] }

    for c in cs.keys():

        cs_counts[ "city"].append( cs[ c ]["city"] )
        cs_counts[ "country"].append( cs[ c ]["country"] )
        cs_counts[ "label"].append( cs[ c ]["label"] )
        cs_counts[ "latitude"].append( cs[ c ]["latitude"] )
        cs_counts[ "longitude"].append( cs[ c ]["longitude"] )
        cs_counts[ "count"].append( cs[ c ][ "count" ] )
        cs_counts[ "ISO-3166-alpha3"].append( cs[ c ][ "ISO-3166-alpha3" ] )

        print(("{}: {} samples").format(cs[ c ]["label"], cs[ c ]["count"]))

    return(cs_counts)


################################################################################

def _aggregate_country_counts(geo_s):

    countries = {  }
    for g in geo_s:
        if "ISO-3166-alpha3" in g:
            if g["ISO-3166-alpha3"] in countries:
                countries[ g["ISO-3166-alpha3"] ][ "count" ] += 1
            else:
                countries[ g["ISO-3166-alpha3"] ] = {
                    "count": 1,
                    "country": g["country"],
                    "ISO-3166-alpha3": g[ "ISO-3166-alpha3" ]
                }

    country_counts = { "country": [ ], "count": [ ], "ISO-3166-alpha3": [ ] }

    for c in countries.keys():

        country_counts[ "country"].append( countries[ c ]["country"] )
        country_counts[ "count"].append( countries[ c ][ "count" ] )
        country_counts[ "ISO-3166-alpha3"].append( countries[ c ][ "ISO-3166-alpha3" ] )

        print(("{} ({}): {} samples").format(countries[ c ]["country"], countries[ c ][ "ISO-3166-alpha3" ], countries[ c ]["count"]))

    return(country_counts)
