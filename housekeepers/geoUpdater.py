#!/usr/local/bin/python3

from os import path, environ, pardir
from progress.bar import Bar
from pymongo import MongoClient

from bycon import BYC, BYC_DBS
from byconServiceLibs import ByconTSVreader

dir_path = path.dirname( path.abspath(__file__) )
geo_rsrc_path = path.join( dir_path, pardir, "rsrc", "geolocs" )

# https://download.geonames.org/export/dump/cities500.zip

"""
## Cities

* https://download.geonames.org/export/dump/cities500.zip

The main 'geoname' table has the following fields :
---------------------------------------------------
geonameid         : integer id of record in geonames database
name              : name of geographical point (utf8) varchar(200)
asciiname         : name of geographical point in plain ascii characters, varchar(200)
alternatenames    : alternatenames, comma separated, ascii names automatically transliterated, convenience attribute from alternatename table, varchar(10000)
latitude          : latitude in decimal degrees (wgs84)
longitude         : longitude in decimal degrees (wgs84)
feature class     : see http://www.geonames.org/export/codes.html, char(1)
feature code      : see http://www.geonames.org/export/codes.html, varchar(10)
country code      : ISO-3166 2-letter country code, 2 characters
cc2               : alternate country codes, comma separated, ISO-3166 2-letter country code, 200 characters
admin1 code       : fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)
admin2 code       : code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80) 
admin3 code       : code for third level administrative division, varchar(20)
admin4 code       : code for fourth level administrative division, varchar(20)
population        : bigint (8 byte int) 
elevation         : in meters, integer
dem               : digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.
timezone          : the iana timezone id (see file timeZone.txt) varchar(40)
modification date : date of last modification in yyyy-MM-dd format

## Country Info

* https://download.geonames.org/export/dump/countryInfo.txt

#ISO	ISO3	ISO-Numeric	fips	Country	Capital	Area(in sq km)	Population	Continent	tld	CurrencyCode	CurrencyName	Phone	Postal Code Format	Postal Code Regex	Languages	geonameid	neighbours	EquivalentFipsCode

"""

cities_f_n = "cities500.txt"
fieldnames = ["geonameid", "name", "asciiname", "alternatenames", "latitude", "longitude", "feature_class", "feature_code", "country_code", "cc2", "admin1_code", "admin2_code", "admin3_code", "admin4_code", "population", "elevation", "dem", "timezone", "modification_date"]
cities, fieldnames = ByconTSVreader().file_to_dictlist(path.join( geo_rsrc_path, cities_f_n), fieldnames=fieldnames, max_count=0)

countries_f_n = "countryInfo.txt"
fieldnames = ["ISO", "ISO3", "ISO-Numeric", "fips", "Country", "Capital", "Area(in sq km)", "Population", "Continent", "tld", "CurrencyCode", "CurrencyName", "Phone", "Postal Code Format", "Postal Code Regex", "Languages", "geonameid", "neighbours", "EquivalentFipsCode"]
countries, fieldnames = ByconTSVreader().file_to_dictlist(path.join( geo_rsrc_path, countries_f_n), fieldnames=fieldnames, max_count=0)

continents ={
	"AF": "Africa",
	"AN": "Antarctica",
	"AS": "Asia",
	"EU": "Europe",
	"NA": "North America",
	"OC": "Oceania",
	"SA": "South America",
	"AT": "Atlantis"
}

atlantis = {
		"geonameid": "0",
		"id": "atlantis::bermudatriangle",
		"geo_source": "custom entry",
		"geo_location": {
			"type": 'Feature',
			"geometry": { "type": 'Point', "coordinates": [ -71, 25 ] },
			"properties": {
				"id": "atlantis::bermudatriangle::-71::25",
				"label": f"Atlantis, Bermuda Triangle",
				"ISO3166alpha2": "00",
				"ISO3166alpha3": "000",
				"city": "Atlantis",
				"continent": "AT",
				"country": "Bermuda Triangle"
		}
	  }
	}


c_by_code = {}
for c in countries:
	c_by_code.update({c.get("ISO", "__none__"): c})

bar = Bar(f"=> reading cities", max=len(cities), suffix='%(percent)d%%'+" of "+str(len(cities)) )

geolocs = [atlantis]
for c in cities:
	bar.next()
	country_code = c.get("country_code", "__none__")
	if not (country := c_by_code.get(country_code)):
		continue

	city = c.get("asciiname", "")
	country_name = country.get("Country", "___none___")
	ISO3166alpha2 = country_code
	ISO3166alpha3 = country.get("ISO3", "")
	continent_code = country.get("Continent", "___none___")
	geo_long = float(c.get("longitude", 0))
	geo_lat = float(c.get("latitude", 0))
	geoprov_id = f"{city}::{country_name}::{geo_long}::{geo_lat}".lower().replace(" ", "")
	geo_city = {
		"geonameid": c.get("geonameid"),
		"geo_source": f"geonames.org {cities_f_n} and {countries_f_n}",
		"geo_location": {
			"type": 'Feature',
			"geometry": { "type": 'Point', "coordinates": [ geo_long, geo_lat ] },
			"properties": {
				"id": geoprov_id,
				"label": f"{city}, {country_name}",
				"ISO3166alpha2": ISO3166alpha2,
				"ISO3166alpha3": ISO3166alpha3,
				"city": city,
				"continent": continents.get(continent_code, "___none___"),
				"country": country_name
		}
	  }
	}

	geolocs.append(geo_city)

bar.finish()

m_h 		= BYC_DBS["mongodb_host"]
m_d 		= BYC_DBS["services_db"]
m_c 		= BYC_DBS.get("collections", {}).get("geolocs")
geo_coll 	= MongoClient(host=m_h)[m_d][m_c]

if not BYC["TEST_MODE"]:
	bar = Bar(f"=> updating cities", max=len(geolocs), suffix='%(percent)d%%'+" of "+str(len(geolocs)) )
	# modify later to keep custom "geo_source"
	geo_coll.delete_many({})
	for g in geolocs:
		bar.next()
		geo_coll.insert_one(g)
	bar.finish()
else:
	print(f"Would update geolocations collection with {len(geolocs)} entries")
	pass
