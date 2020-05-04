from os import path
from pymongo import MongoClient
import plotly
import plotly.graph_objects as go
import pandas as pd
from urllib.request import urlopen
import json

################################################################################

def plot_worldmap(**kwargs):

    plotly.io.orca.config.executable = "/usr/local/bin/orca"
    dataset_id = kwargs[ "dataset_id" ]
    dash = kwargs[ "config" ][ "const" ][ "dash_sep" ]
    args = kwargs[ "args" ]
    label = ""
    if args.label:
        label = args.label

    dataset_id = kwargs[ "dataset_id" ]
    query = { "_id": { "$in": kwargs[ "biosamples::_id" ] } }
    bios_coll = MongoClient( )[ dataset_id ][ "biosamples" ]

    mapplot = path.join( kwargs[ "config" ][ "paths" ][ "out" ], dash.join([ dataset_id, label, "map.svg" ]) )
    mapdata = path.join( kwargs[ "config" ][ "paths" ][ "out" ], dash.join([ dataset_id, label, "mapdata.tsv" ]) )    

    geo_s = [ ]
    for bios in bios_coll.find(query):
        if "provenance" in bios:
            if "geo" in bios[ "provenance" ]:
                geo_s.append(bios["provenance"]["geo"])

    country_counts = _aggregate_country_counts(geo_s)
    all_samples = len( kwargs[ "biosamples::_id" ] )
    map_samples = sum( country_counts["count"] )
    map_countries = len(country_counts["country"])
 
    df = pd.DataFrame(data=country_counts)
    df.to_csv(mapdata, sep='\t', index=False)

    fig = go.Figure(data=go.Choropleth(
        locations = df['country'],
        locationmode = "country names",
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

    fig.update_layout( title_text=("{} Mapped Samples, from {} Countries").format(map_samples, map_countries) )
    fig.update_geos( landcolor = 'rgb(255,252,225)' )
    fig.update_geos( fitbounds="locations" )
    fig.show()
    try:
        fig.write_image(mapplot)
    except Exception as e:
        print(e)

################################################################################

def _aggregate_country_counts(geo_s):

    countries = {  }
    for g in geo_s:
        if "country" in g:
            if g["country"] in countries:
                countries[ g["country"] ] += 1
            else:
                countries[ g["country"] ] = 1

    country_counts = { "country": [ ], "count": [ ] }

    for key, value in countries.items():

        country_counts[ "country"].append(key)
        country_counts[ "count"].append(value)

    return(country_counts)