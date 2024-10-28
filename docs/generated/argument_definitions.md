# `bycon` Arguments and Parameters
The following is a list of arguments and parameters used in the `bycon` package as well as the `byconaut` tools.
## Definitions
### `user_name` 
**type:** string    
**pattern:** `^\w+$`    
**cmdFlags:** `--userName`    
**description:**
faking a user name    

### `test_mode` 
**type:** boolean    
**cmdFlags:** `-t,--testMode`    
**description:**
test setting, i.e. returning some random documents    
**default:** `False`    

### `skip` 
**type:** integer    
**cmdFlags:** `--skip`    
**description:**
pages to be skipped    
**default:** `0`    

### `limit` 
**type:** integer    
**cmdFlags:** `-l,--limit`    
**description:**
limit number of documents; a value of 0 sets to unlimited    
**default:** `200`    
**local:** 0    

### `requested_granularity` 
**type:** string    
**pattern:** `^\w+$`    
**description:**
The requested granularity of the beacon    
**cmdFlags:** `--requestedGranularity`    
**default:** `record`    

### `request_entity_path_id` 
**type:** string    
**cmdFlags:** `--requestEntityPathId`    
**description:**
    
* data entry point, equal to the first REST path element in Beacon     
* this only is used for command-line tests instead of the REST path
  value seen by the stack in web server mode    

### `response_entity_path_id` 
**type:** string    
**cmdFlags:** `--responseEntityPathId`    
**description:**
    
* optional data delivery entry point, for {id} paths     
* for command line (see above), but also potentially for selecting
  a special response entity in byconaut services (e.g. `indviduals`
  in `/sampletable/`)    

### `requested_schema` 
**type:** string    
**cmdFlags:** `--requestedSchema`    
**description:**
requested schema, e.g. biosample    

### `include_resultset_responses` 
**type:** string    
**cmdFlags:** `--includeResultsetResponses`    
**description:**
    
* include resultset responses, e.g. HIT, MISS     
* kind of a holdover from Beacon pre-v1 but HIT & ALL might have
  some use in networks    
**default:** `HIT`    

### `dataset_ids` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `-d,--datasetIds`    
**description:**
dataset ids    

### `cohort_ids` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--cohortIds`    
**description:**
cohort ids    

### `filters` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--filters`    
**description:**
prefixed filter values, comma concatenated; or objects in POST    

### `filter_precision` 
**type:** string    
**cmdFlags:** `--filterPrecision`    
**description:**
either `start` or `exact` for matching filter values    
**default:** `exact`    

### `filter_logic` 
**type:** string    
**cmdFlags:** `--filterLogic`    
**description:**
Global for either OR or AND (translated to the MongoDB $and etc.). The Beacon protocol only knows AND.    
**default:** `AND`    

### `include_descendant_terms` 
**type:** boolean    
**cmdFlags:** `--includeDescendantTerms`    
**description:**
global treatment of descendant terms    
**default:** `True`    

### `assembly_id` 
**type:** string    
**pattern:** `^\w+?[\w\-\.]*?\w*?$`    
**db_key:** assembly_id    
**cmdFlags:** `--assemblyId`    
**description:**
assembly id; currently not used in bycon's version    

### `reference_name` 
**type:** string    
**db_key:** location.sequence_id    
**pattern:** `^\w+.*?\w?$`    
**cmdFlags:** `--referenceName`    
**description:**
chromosome    

### `mate_name` 
**type:** string    
**db_key:** adjoined_sequences.sequence_id    
**pattern:** `^\w+.*?\w?$`    
**cmdFlags:** `--mateName`    
**description:**
chromosome    

### `reference_bases` 
**type:** string    
**db_key:** reference_sequence    
**pattern:** `^[ACGTN]+$`    
**cmdFlags:** `--referenceBases`    
**description:**
reference bases    

### `alternate_bases` 
**type:** string    
**db_key:** sequence    
**pattern:** `^[ACGTN]+$`    
**cmdFlags:** `--alternateBases`    
**description:**
alternate bases    

### `variant_type` 
**type:** string    
**db_key:** variant_state.id    
**pattern:** `^\w+[\w \-\:]\w+?$`    
**cmdFlags:** `--variantType`    
**description:**
variant type, e.g. DUP    

### `start` 
**type:** array    
**db_key:** location.start    
**items:**  
    - `type`: `integer`      
    - `pattern`: `^\d+?$`    
**cmdFlags:** `--start`    
**description:**
genomic start position    

### `end` 
**type:** array    
**db_key:** location.end    
**items:**  
    - `type`: `integer`      
    - `pattern`: `^\d+?$`    
**cmdFlags:** `--end`    
**description:**
genomic end position    

### `mate_start` 
**type:** integer    
**db_key:** adjoined_sequences.start    
**pattern:** `^\d+?$`    
**cmdFlags:** `--mateStart`    
**description:**
genomic start position of fusion partner breakpoint region    

### `mate_end` 
**type:** integer    
**db_key:** adjoined_sequences.end    
**pattern:** `^\d+?$`    
**cmdFlags:** `--MateEnd`    
**description:**
genomic end position of fusion partner breakpoint region    

### `variant_min_length` 
**type:** integer    
**db_key:** info.var_length    
**pattern:** `^\d+?$`    
**cmdFlags:** `--variantMinLength`    
**description:**
The minimal variant length in bases e.g. for CNV queries.    

### `variant_max_length` 
**type:** integer    
**db_key:** info.var_length    
**pattern:** `^\d+?$`    
**cmdFlags:** `--variantMaxLength`    
**description:**
The maximum variant length in bases e.g. for CNV queries.    

### `gene_id` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w+?(\w+?(\-\w+?)?)?$`    
**db_key:** None    
**cmdFlags:** `--geneId`    
**description:**
gene id    

### `aminoacid_change` 
**type:** string    
**db_key:** molecular_attributes.aminoacid_changes    
**pattern:** `^\w+?$`    
**examples:** `V600E,M734V,G244A`    
**cmdFlags:** `--aminoacidChange`    
**description:**
Aminoacid alteration in 1 letter format    

### `genomic_allele_short_form` 
**type:** string    
**db_key:** identifiers.genomicHGVS_id    
**pattern:** `^\w+.*\w$`    
**examples:** `NC_000017.11:g.7674232C>G`    
**cmdFlags:** `--genomicAlleleShortForm`    
**description:**
Genomic HGVSId descriptor    

### `variant_query_digests` 
**type:** array    
**db_key:** None    
**items:**  
    - `type`: `string`      
    - `pattern`: `^(?:chro?)?([12]?[\dXY]):(\d+?(?:-\d+?)?)(?:--(\d+?(?:-\d+?)?))?(?::([\w\:\>]+?))?$`    
**cmdFlags:** `--variantQueryDigests`    
**examples:** `9:9000001-21975098--21967753-24000000:DEL`    
**description:**
EXPERIMENTAL Variant query digest-style short form    

### `variant_multi_pars` 
**type:** array    
**db_key:** None    
**items:**  
    - `type`: `object`    
**cmdFlags:** `--variantMultiPars`    
**description:**
EXPERIMENTAL List of multiple variant queries, for POST    

### `variant_internal_id` 
**type:** string    
**db_key:** variant_internal_id    
**pattern:** `^\w[\w\:\-\,]+?\w$`    
**examples:** `11:52900000-134452384:EFO_0030067`    
**cmdFlags:** `--variantInternalId`    
**description:**
An id value used for all variant instances of the same composition; a kind of `digest`    

### `accessid` 
**type:** string    
**db_key:** id    
**pattern:** `^\w[\w\-]+?\w$`    
**examples:** `b59857bc-0c4a-4ac8-804b-6596c6566494`    
**cmdFlags:** `--accessid`    
**description:**
An accessid for retrieving handovers etc.    

### `file_id` 
**type:** string    
**pattern:** `^\w[\w\-]+?\w$`    
**examples:** `90e19951-1443-4fa8-8e0b-6b5d8c5e45cc`    
**cmdFlags:** `--fileId`    
**description:**
A file id e.g. as generated by the uploader service    

### `id` 
**type:** string    
**db_key:** id    
**pattern:** `^\w[\w\:\-\,]+?\w$`    
**examples:** `pgxvar-5bab576a727983b2e00b8d32,pgxind-kftx25eh`    
**cmdFlags:** `--id`    
**description:**
An id; this parameter only makes sense for specific REST entry types    

### `ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w:-]+\w$`    
**cmdFlags:** `--ids`    
**description:**
One or more ids; this parameter only makes sense for specific REST entry types    

### `biosample_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w:-]+\w$`    
**byc_entity:** biosample    
**cmdFlags:** `--biosampleIds`    
**description:**
biosample ids    

### `analysis_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w:-]+\w$`    
**byc_entity:** analysis    
**cmdFlags:** `--analysisIds`    
**description:**
analysis ids    

### `individual_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w:-]+\w$`    
**byc_entity:** individual    
**cmdFlags:** `--individualIds`    
**description:**
subject ids    

### `variant_ids` 
**type:** array    
**items:**  
    - `type`: `string`      
    - `pattern`: `^\w[\w:-]+\w$`    
**byc_entity:** genomicVariant    
**cmdFlags:** `--variantIds`    
**description:**
variant ids    

### `debug_mode` 
**type:** boolean    
**cmdFlags:** `--debugMode`    
**description:**
debug setting    
**default:** `False`    

### `show_help` 
**type:** boolean    
**cmdFlags:** `--showHelp`    
**description:**
specific help display    
**default:** `False`    

### `test_mode_count` 
**type:** integer    
**cmdFlags:** `--testModeCount`    
**description:**
setting the number of documents reurned in test mode    
**default:** `5`    

### `output` 
**type:** string    
**cmdFlags:** `--output`    
**description:**
For defining a special output format, mostly for `byconaut` services use. Examples:
    
* `cnvstats`, for `analyses`, to present some CNV statistics     
* `pgxseg`, using the `.pgxseg` variant file format     
* `text`, for some services to deliver a text table instead of JSON     
* in byconaut for the target database when copying...    

### `include_handovers` 
**type:** boolean    
**default:** `True`    
**cmdFlags:** `--includeHandovers`    
**description:**
only used for web requests & testing    

### `method` 
**type:** string    
**cmdFlags:** `--method`    
**description:**
special method    
**default:** `None`    

### `group_by` 
**type:** string    
**cmdFlags:** `--groupBy`    
**description:**
group parameter e.g. for subset splitting    
**default:** `text`    

### `mode` 
**type:** string    
**cmdFlags:** `-m,--mode`    
**description:**
mode, e.g. file type    

### `update` 
**type:** boolean    
**cmdFlags:** `-u,--update`    
**description:**
update existing records - might be deprecated; only used for publications    
**default:** `False`    

### `force` 
**type:** boolean    
**cmdFlags:** `--force`    
**description:**
force mode, e.g. for update or insert (cmd line)    
**default:** `False`    

### `inputfile` 
**type:** string    
**cmdFlags:** `-i,--inputfile`    
**description:**
a custom file to specify input data, usually tab-delimited with special header    

### `outputdir` 
**type:** string    
**cmdFlags:** `--outputdir`    
**description:**
output directory where supported (cmd line)    

### `outputfile` 
**type:** string    
**cmdFlags:** `-o,--outputfile`    
**description:**
output file where supported (cmd line)    

### `min_number` 
**type:** integer    
**cmdFlags:** `--minNumber`    
**description:**
minimal number, e.g. for collations, where supported    
**default:** `0`    

### `delivery_keys` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--deliveryKeys`    
**description:**
delivery keys to force only some parameters in custom exporters    

### `collation_types` 
**type:** array    
**items:**  
    - `type`: `string`    
**cmdFlags:** `--collationTypes`    
**description:**
selected collation types, e.g. "EFO"    

### `selected_beacons` 
**type:** array    
**items:**  
    - `type`: `string`    

### `genome_binning` 
**type:** string    
**default:** `1Mb`    
**cmdFlags:** `--genomeBinning`    
**description:**
one of the predefined genome binning keys - default 1Mb    

### `cyto_bands` 
**type:** string    
**pattern:** `^(?:chro?)?([12]?[\dXY])([pq](?:(?:ter)|(?:cen)|(?:[1-4](?:\d(?:\.\d\d*?)?)?)?))?\-?([pq](?:(?:cen)|(?:ter)|(?:[1-4](?:\d(?:\.\d\d*?)?)?)?))?$`    
**db_key:** None    
**cmdFlags:** `--cytoBands`    
**description:**
cytobands, e.g. 8q21q24.1    

### `chro_bases` 
**type:** string    
**pattern:** `^(chro?)?([12]?[\dXY])\:(\d+?)(\-(\d+?))?$`    
**db_key:** None    
**cmdFlags:** `--chroBases`    
**description:**
only for the cytoband converter ... e.g. 8:0-120000000    

### `city` 
**type:** string    
**cmdFlags:** `-c,--city`    
**description:**
only for the geolocations...    

### `geo_latitude` 
**type:** number    
**cmdFlags:** `--geoLatitude`    
**description:**
only for the geolocations...    

### `geo_longitude` 
**type:** number    
**cmdFlags:** `--geoLongitude`    
**description:**
only for the geolocations...    

### `geo_distance` 
**type:** integer    
**cmdFlags:** `--geoDistance`    
**description:**
only for the geolocations...    

### `plot_pars` 
**type:** string    
**cmdFlags:** `--plotPars`    
**description:**
plot parameters in form `par=value` concatenated by `::`    

### `plot_type` 
**type:** string    
**cmdFlags:** `--plotType`    
**description:**
plot type (histoplot, samplesplot, arrayplot - more?)    
**default:** `None`    
