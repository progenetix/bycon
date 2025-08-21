### Argument Definitions
#### `user_name` 
**description:**
TODO: Temporary(?) for authentication testing.    
**type:** string    
**pattern:** `^\w+$`    
**cmdFlags:** `--userName`    
**in:** query    

#### `test_mode` 
**description:**
Activates the Beacon test setting, i.e. returning some random documents    
**type:** boolean    
**cmdFlags:** `-t,--testMode`    
**default:** `False`    
**in:** query    
**beacon_query:** True    

#### `skip` 
**description:**
Number of pages to be skipped.    
**type:** integer    
**cmdFlags:** `--skip`    
**default:** `0`    
**in:** query    

#### `limit` 
**type:** integer    
**cmdFlags:** `-l,--limit`    
**description:**
limit number of documents; a value of 0 sets to unlimited    
**default:** `200`    
**local:** 0    
**in:** query    

#### `paginate_results` 
**description:**
Custom bycon parameter used for paginating results in some bycon services.    
**type:** boolean    
**cmdFlags:** `--paginateResults`    
**default:** `True`    

#### `requested_granularity` 
**description:**
The requested granularity of the beacon    
**type:** string    
**enum:** `record,count,boolean`    
**pattern:** `^\w+$`    
**cmdFlags:** `--requestedGranularity`    
**default:** `record`    
**in:** query    
**examples:** `{'emptyValue': {'value': '', 'summary': 'Granularity of the response'}},{'record': {'value': 'record', 'summary': 'Data record'}},{'count': {'value': 'count', 'summary': 'Count of the matched records'}},{'boolean': {'value': 'boolean', 'summary': 'Boolean for match / no match'}}`    

#### `request_entity_path_id` 
**description:**
    
* data entry point, equal to the first REST path element in Beacon     
* this only is used for command-line tests instead of the REST path
  value seen by the stack in web server mode    
**type:** string    
**cmdFlags:** `-p,--requestEntityPathId`    
**default:** `info`    

#### `response_entity_path_id` 
**description:**
    
* optional data delivery entry point, for {id} paths     
* for command line (see above), but also potentially for selecting
  a special response entity in byconaut services (e.g. `indviduals`
  in `/sampletable/`)    
**type:** string    
**cmdFlags:** `-r,--responseEntityPathId`    

#### `include_resultset_responses` 
**type:** string    
**cmdFlags:** `--includeResultsetResponses`    
**description:**
    
* include resultset responses, e.g. HIT, MISS     
* kind of a holdover from Beacon pre-v1 but HIT & ALL might have
  some use in networks    
**default:** `HIT`    
**in:** query    

#### `dataset_ids` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `-d,--datasetIds`    
**description:**
dataset ids    

#### `cohort_ids` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--cohortIds`    
**description:**
cohort ids    

#### `filters` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--filters`    
**description:**
prefixed filter values, comma concatenated; or objects in POST    
**in:** query    
**beacon_query:** True    
**vqs_query:** True    
**examples:** `{'emptyValue': {'value': '', 'summary': 'A Beacon filter value, e.g. a CURIE for a disease code'}},{'NCIT': {'value': ['NCIT:C9335'], 'summary': 'A neoplasia disease code (CURIE format)'}},{'pubmed': {'value': ['pubmed:28966033'], 'summary': 'A publiction identifier (CURIE format)'}}`    

#### `filter_precision` 
**type:** string    
**cmdFlags:** `--filterPrecision`    
**description:**
either `start` or `exact` for matching filter values    
**default:** `exact`    

#### `aggregation_terms` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--aggregationTerms`    
**description:**
Experimental for Beacon v2+ for indicating which summaries to provide    

#### `filter_logic` 
**type:** string    
**cmdFlags:** `--filterLogic`    
**description:**
Global for either OR or AND (translated to the MongoDB $and etc.). The Beacon protocol only knows AND.    
**default:** `AND`    

#### `include_descendant_terms` 
**type:** boolean    
**cmdFlags:** `--includeDescendantTerms`    
**description:**
global treatment of descendant terms    
**default:** `True`    

#### `vrs_type` 
**type:** string    
**pattern:** `^\w+$`    
**db_key:** type    
**cmdFlags:** `--vrsType`    
**description:**
VRS variant schema type, e.g. `Allele` or `CopyNumberChange`    
**beacon_query:** False    
**vqs_query:** True    
**in:** query    

#### `reference_accession` 
**type:** string    
**db_key:** location.sequence_id    
**pattern:** `^\w+.*?\w?$`    
**cmdFlags:** `--referenceAccession`    
**description:**
reference accession, i.e. a versioned sequence reference ID    
**beacon_query:** False    
**vqs_query:** True    
**in:** query    

#### `copy_change` 
**type:** string    
**db_key:** variant_state.id    
**pattern:** `^\w+[\w \-\:]\w+?$`    
**cmdFlags:** `--copyChange`    
**description:**
variant type, e.g. EFO:0030067 or DUP    
**beacon_query:** False    
**vqs_query:** True    
**in:** query    

#### `sequence_length` 
**type:** array    
**db_key:** info.var_length    
**items:**  
    - `type`: `integer`      
    - `pattern`: `^\d+?$`    
**cmdFlags:** `--sequenceLength`    
**description:**
    
* length (range) of variant sequence
    
* should replace variant_min_length and variant_max_length    
**beacon_query:** False    
**vqs_query:** True    
**in:** query    

#### `breakpoint_range` 
**type:** array    
**db_key:** adjoined_sequences.start    
**items:**  
    - `type`: `integer`      
    - `pattern`: `^\d+?$`    
**minItems:** 2    
**maxItems:** 2    
**cmdFlags:** `--breakpointRange`    
**description:**
range for breakpoint or lower chromosome position in adjacency    
**beacon_query:** False    
**vqs_query:** True    
**in:** query    

#### `adjacency_accession` 
**type:** string    
**db_key:** adjoined_sequences.sequence_id    
**pattern:** `^\w+.*?\w?$`    
**cmdFlags:** `--adjacencyAccession`    
**description:**
adjacency accession, i.e. a versioned sequence reference ID    
**beacon_query:** False    
**vqs_query:** True    
**in:** query    

#### `adjacency_range` 
**type:** array    
**db_key:** adjoined_sequences.start    
**items:**  
    - `type`: `integer`      
    - `pattern`: `^\d+?$`    
**minItems:** 2    
**maxItems:** 2    
**cmdFlags:** `--adjacencyRange`    
**description:**
range for higher chromosome position in adjacency    
**beacon_query:** False    
**vqs_query:** True    
**in:** query    

#### `assembly_id` 
**type:** string    
**pattern:** `^\w+?[\w\-\.]*?\w*?$`    
**db_key:** assembly_id    
**cmdFlags:** `--assemblyId`    
**description:**
assembly id; currently not used in bycon's version    

#### `reference_name` 
**type:** string    
**db_key:** location.sequence_id    
**pattern:** `^\w+.*?\w?$`    
**cmdFlags:** `--referenceName`    
**description:**
chromosome    
**beacon_query:** True    
**in:** query    
**examples:** `{'emptyValue': {'value': '', 'summary': 'A versioned reference ID or a chromsome name / number'}},{'chromosome': {'value': '9', 'summary': 'chromsome 9'}}`    

#### `mate_name` 
**type:** string    
**db_key:** adjoined_sequences.sequence_id    
**pattern:** `^\w+.*?\w?$`    
**cmdFlags:** `--mateName`    
**description:**
chromosome    
**beacon_query:** True    
**in:** query    
**examples:** `{'emptyValue': {'value': '', 'summary': 'A versioned reference ID or a chromsome name / number'}}`    

#### `reference_bases` 
**type:** string    
**db_key:** state.reference_sequence    
**pattern:** `^[ACGTN]+$`    
**cmdFlags:** `--referenceBases`    
**description:**
reference bases    
**beacon_query:** True    
**in:** query    

#### `alternate_bases` 
**type:** string    
**db_key:** state.sequence    
**pattern:** `^[ACGTN]+$`    
**cmdFlags:** `--alternateBases`    
**description:**
alternate bases    
**beacon_query:** True    
**in:** query    

#### `variant_type` 
**type:** string    
**db_key:** variant_state.id    
**pattern:** `^\w+[\w \-\:]\w+?$`    
**cmdFlags:** `--variantType`    
**description:**
variant type, e.g. EFO:0030067 or DUP    
**beacon_query:** True    
**in:** query    
**examples:** `{'emptyValue': {'value': '', 'summary': 'An EFO or SO code in CURIE format, or a VCF-style label'}},{'EFOhllossCNV': {'value': 'EFO:0030067', 'summary': 'high-level copy number loss'}},{'VCFdup': {'value': 'DUP', 'summary': 'copy number duplication'}}`    

#### `start` 
**type:** array    
**db_key:** location.start    
**items:**  
    - `type`: `integer`      
    - `pattern`: `^\d+?$`    
**minItems:** 1    
**maxItems:** 2    
**cmdFlags:** `--start`    
**description:**
genomic start position    
**beacon_query:** True    
**vqs_query:** True    
**in:** query    

#### `end` 
**type:** array    
**db_key:** location.end    
**items:**  
    - `type`: `integer`      
    - `pattern`: `^\d+?$`    
**minItems:** 1    
**maxItems:** 2    
**cmdFlags:** `--end`    
**description:**
genomic end position    
**beacon_query:** True    
**vqs_query:** True    
**in:** query    

#### `mate_start` 
**type:** integer    
**db_key:** adjoined_sequences.start    
**pattern:** `^\d+?$`    
**cmdFlags:** `--mateStart`    
**description:**
genomic start position of fusion partner breakpoint region    

#### `mate_end` 
**type:** integer    
**db_key:** adjoined_sequences.end    
**pattern:** `^\d+?$`    
**cmdFlags:** `--MateEnd`    
**description:**
genomic end position of fusion partner breakpoint region    

#### `variant_min_length` 
**type:** integer    
**db_key:** info.var_length    
**pattern:** `^\d+?$`    
**cmdFlags:** `--variantMinLength`    
**description:**
The minimal variant length in bases e.g. for CNV queries.    
**beacon_query:** True    
**in:** query    

#### `variant_max_length` 
**type:** integer    
**db_key:** info.var_length    
**pattern:** `^\d+?$`    
**cmdFlags:** `--variantMaxLength`    
**description:**
The maximum variant length in bases e.g. for CNV queries.    
**beacon_query:** True    
**in:** query    

#### `gene_id` 
**type:** array    
**items:**  
    - `pattern`: `^\w+?(\w+?(\-\w+?)?)?$`      
    - `type`: `string`    
**db_key:** None    
**cmdFlags:** `--geneId`    
**description:**
one or more (comma concatenated) gene ids    
**beacon_query:** True    
**vqs_query:** True    
**in:** query    
**examples:** `{'emptyValue': {'value': [''], 'summary': 'A HUGO gene symbol'}},{'TP53': {'value': ['TP53'], 'summary': 'TP53 gene identifier'}},{'CDKN2A': {'value': ['CDKN2A'], 'summary': 'CDKN2A gene identifier'}}`    

#### `aminoacid_change` 
**type:** string    
**db_key:** molecular_attributes.aminoacid_changes    
**pattern:** `^\w+?$`    
**cmdFlags:** `--aminoacidChange`    
**description:**
Aminoacid alteration in 1 letter format    
**in:** query    
**examples:** `{'emptyValue': {'value': '', 'summary': 'Aminoacid alteration in 1 letter format'}},{'V600E': {'value': 'V600E'}},{'M734V': {'value': 'M734V'}},{'G244A': {'value': 'G244A'}}`    

#### `genomic_allele_short_form` 
**type:** string    
**db_key:** identifiers.genomicHGVS_id    
**pattern:** `^\w+.*\w$`    
**cmdFlags:** `--genomicAlleleShortForm`    
**description:**
Genomic HGVSId descriptor    
**in:** query    
**examples:** `{'gHGVS': {'value': 'NC_000017.11:g.7674232C>G'}}`    

#### `variant_query_digests` 
**type:** array    
**db_key:** None    
**items:**  
    - `type`: `string`      
    - `pattern`: `^(?:chro?)?([12]?[\dXY]):(\d+?(?:-\d+?)?)(?:--(\d+?(?:-\d+?)?))?(?::([\w\:\>]+?))?$`    
**cmdFlags:** `--variantQueryDigests`    
**description:**
EXPERIMENTAL Variant query digest-style short form    
**examples:** `{'DELdigest': {'value': '9:9000001-21975098--21967753-24000000:DEL'}}`    

#### `variant_multi_pars` 
**type:** array    
**db_key:** None    
**items:**  
    - `type`: `object`    
**cmdFlags:** `--variantMultiPars`    
**description:**
EXPERIMENTAL List of multiple variant queries, for POST    

#### `variant_internal_id` 
**type:** string    
**db_key:** variant_internal_id    
**pattern:** `^\w[\w\:\-\,]+?\w$`    
**cmdFlags:** `--variantInternalId`    
**description:**
An id value used for all variant instances of the same composition; a kind of `digest`    
**examples:** `{'EFO_0030067': {'value': '11:52900000-134452384:EFO_0030067'}}`    

#### `accessid` 
**type:** string    
**db_key:** id    
**pattern:** `^\w[\w\-]+?\w$`    
**cmdFlags:** `--accessid`    
**description:**
An accessid for retrieving handovers etc.    
**examples:** `{'accessid': {'value': 'b59857bc-0c4a-4ac8-804b-6596c6566494'}}`    

#### `file_id` 
**type:** string    
**pattern:** `^\w[\w\-]+?\w$`    
**cmdFlags:** `--fileId`    
**description:**
A file id e.g. as generated by the uploader service    
**examples:** `{'FileID': {'value': '90e19951-1443-4fa8-8e0b-6b5d8c5e45cc'}}`    

#### `id` 
**type:** string    
**db_key:** id    
**pattern:** `^\w[\w\:\-\,]+?\w$`    
**cmdFlags:** `--id`    
**description:**
An id; this parameter only makes sense for specific REST entry types    
**in:** path    
**examples:** `{'variant_id': {'value': 'pgxvar-5bab576a727983b2e00b8d32', 'summary': 'An internal variant ID', 'in_paths': ['g_variants']}},{'individual_id': {'value': 'pgxind-kftx25eh', 'summary': 'An internal ID for an individual / subject', 'in_paths': ['individuals']}},{'biosample_id': {'value': 'pgxbs-kftviphc', 'summary': 'An internal biosample ID', 'in_paths': ['biosamples']}},{'analysis_id': {'value': 'pgxcs-kftwaay4', 'summary': 'An internal analysis ID', 'in_paths': ['analyses']}}`    

#### `path_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w,:-]+\w$`    
**cmdFlags:** `--pathIds`    
**description:**
One or more ids provided in the path for specific REST entry types    

#### `biosample_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w,:-]+\w$`    
**byc_entity:** biosample    
**cmdFlags:** `--biosampleIds`    
**description:**
biosample ids    

#### `analysis_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w,:-]+\w$`    
**byc_entity:** analysis    
**cmdFlags:** `--analysisIds`    
**description:**
analysis ids    

#### `individual_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w,:-]+\w$`    
**byc_entity:** individual    
**cmdFlags:** `--individualIds`    
**description:**
subject ids    

#### `variant_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w,:-]+\w$`    
**byc_entity:** genomicVariant    
**cmdFlags:** `--variantIds`    
**description:**
variant ids    

#### `debug_mode` 
**type:** boolean    
**cmdFlags:** `--debugMode`    
**description:**
debug setting    
**default:** `False`    

#### `show_help` 
**type:** boolean    
**cmdFlags:** `--showHelp`    
**description:**
specific help display    
**default:** `False`    

#### `test_mode_count` 
**type:** integer    
**cmdFlags:** `--testModeCount`    
**description:**
setting the number of documents reurned in test mode    
**default:** `5`    

#### `output` 
**type:** string    
**cmdFlags:** `--output`    
**description:**
For defining a special output format, mostly for `byconaut` services use. Examples:
    
* `cnvstats`, for `analyses`, to present some CNV statistics     
* `pgxseg`, using the `.pgxseg` variant file format     
* `text`, for some services to deliver a text table instead of JSON     
* for the target database when copying...    

#### `include_handovers` 
**type:** boolean    
**default:** `True`    
**cmdFlags:** `--includeHandovers`    
**description:**
only used for web requests & testing    

#### `method` 
**type:** string    
**cmdFlags:** `--method`    
**description:**
special method    
**default:** `None`    

#### `group_by` 
**type:** string    
**cmdFlags:** `--groupBy`    
**description:**
group parameter e.g. for subset splitting    
**default:** `text`    

#### `mode` 
**type:** string    
**cmdFlags:** `-m,--mode`    
**description:**
mode, e.g. file type    

#### `update` 
**type:** boolean    
**cmdFlags:** `-u,--update`    
**description:**
update existing records - might be deprecated; only used for publications    
**default:** `False`    

#### `force` 
**type:** boolean    
**cmdFlags:** `--force`    
**description:**
force mode, e.g. for update or insert (cmd line)    
**default:** `False`    

#### `inputfile` 
**type:** string    
**cmdFlags:** `-i,--inputfile`    
**description:**
a custom file to specify input data, usually tab-delimited with special header    

#### `outputdir` 
**type:** string    
**cmdFlags:** `--outputdir`    
**description:**
output directory where supported (cmd line)    

#### `outputfile` 
**type:** string    
**cmdFlags:** `-o,--outputfile`    
**description:**
output file where supported (cmd line)    

#### `min_number` 
**type:** integer    
**cmdFlags:** `--minNumber`    
**description:**
minimal number, e.g. for collations, where supported    
**default:** `0`    

#### `delivery_keys` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--deliveryKeys`    
**description:**
delivery keys to force only some parameters in custom exporters    

#### `collation_types` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--collationTypes`    
**description:**
selected collation types, e.g. "EFO"    

#### `genome_binning` 
**type:** string    
**default:** `1Mb`    
**cmdFlags:** `--genomeBinning`    
**description:**
one of the predefined genome binning keys - default 1Mb    

#### `cyto_bands` 
**type:** string    
**pattern:** `^(?:chro?)?([12]?[\dXY])([pq](?:(?:ter)|(?:cen)|(?:[1-4](?:\d(?:\.\d\d*?)?)?)?))?\-?([pq](?:(?:cen)|(?:ter)|(?:[1-4](?:\d(?:\.\d\d*?)?)?)?))?$`    
**db_key:** None    
**cmdFlags:** `--cytoBands`    
**description:**
cytobands, e.g. 8q21q24.1    

#### `chro_bases` 
**type:** string    
**pattern:** `^(chro?)?([12]?[\dXY])\:(\d+?)(\-(\d+?))?$`    
**db_key:** None    
**cmdFlags:** `--chroBases`    
**description:**
only for the cytoband converter ... e.g. 8:0-120000000    

#### `city` 
**type:** string    
**cmdFlags:** `--city`    
**description:**
only for the geolocations...    

#### `country` 
**type:** string    
**cmdFlags:** `--country`    
**description:**
only for the geolocations...    

#### `iso3166alpha3` 
**type:** string    
**cmdFlags:** `--iso3166alpha3`    
**description:**
only for the geolocations...    

#### `iso3166alpha2` 
**type:** string    
**cmdFlags:** `--iso3166alpha2`    
**description:**
only for the geolocations...    

#### `geo_latitude` 
**type:** number    
**cmdFlags:** `--geoLatitude`    
**description:**
only for the geolocations...    

#### `geo_longitude` 
**type:** number    
**cmdFlags:** `--geoLongitude`    
**description:**
only for the geolocations...    

#### `geo_distance` 
**type:** integer    
**cmdFlags:** `--geoDistance`    
**default:** `2000`    
**description:**
distance from long, lat point in geolocation queries    

#### `plot_pars` 
**type:** string    
**forceNoSplit:** True    
**cmdFlags:** `--plotPars`    
**description:**
plot parameters in form `par=value` concatenated by `::`    

#### `plot_type` 
**type:** string    
**cmdFlags:** `--plotType`    
**description:**
plot type (histoplot, samplesplot, arrayplot - more?)    
**default:** `histoplot`    
