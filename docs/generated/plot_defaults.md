# Plot Parameters and Information
## Plot Types
### `histoplot` 
**description:**
The default option, used to plot histograms of the CNV frequencies per data collection ("collation") or aggregated sample data.    
**data_key:** interval_frequencies_bundles    
**data_type:** collations    

### `histoheatplot` 
**description:**
A "heatmap" style version of the histogram plot, where a single gain/loss frequency result is transformed into a small heat color strip.    
**data_key:** interval_frequencies_bundles    
**data_type:** collations    

### `histosparkplot` 
**description:**
A version of the histogram with predefined parameters for representing a small and unlabeled plot, e.g. for use in hover previews. As in the normal histogram parameters can be overridden.    
**data_key:** interval_frequencies_bundles    
**data_type:** collations    
**mods:**  
    - `plot_chro_height`: `0`      
    - `plot_title_font_size`: `0`      
    - `plot_area_height`: `18`      
    - `plot_margins`: `0`      
    - `plot_axislab_y_width`: `0`      
    - `plot_grid_stroke`: `0`      
    - `plot_footer_font_size`: `0`      
    - `plot_width`: `480`      
    - `plot_area_opacity`: `0`      
    - `plot_dendrogram_width`: `0`      
    - `plot_labelcol_width`: `0`      
    - `plot_axis_y_max`: `80`    
**modded:** histoplot    

### `samplesplot` 
**description:**
A plot of the called CNV segments per sample, with the samples ordered by their clustering (_i.e._ similarity of binned CNV data).    
**data_key:** callsets_variants_bundles    
**data_type:** samples    

## Plot Parameters
### `plot_id` 
**default:** `genomeplot`    

### `plot_title` 
**description:**
title above the plot    

### `plot_group_by` 
**description:**
group samples in histograms by a filter type (NCIT, PMID...)    
**default:** ``    

### `plot_filter_empty_samples` 
**description:**
By setting to `true` samples w/o data can be removed e.g. from sample plots    
**type:** boolean    
**default:** `False`    

### `force_empty_plot` 
**description:**
By setting to `true` a plot strip will be forced even if there are no CNV samples    
**type:** boolean    
**default:** `False`    

### `plot_cluster_results` 
**description:**
By setting to `false` clustering can be suppressed    
**type:** boolean    
**default:** `True`    

### `plot_samples_cluster_type` 
**description:**
Selection of which measurees are used to generate the clustering matrix
    
* `intcoverage` uses the ~2x3k (gain, loss) 1MB intervals     
* `chrostats` only uses the CNV coverage per chromosomal arm (separately
  for gains and losses)    
**default:** `intcoverage`    
**oneOf:** `chrostats,intcoverage`    

### `plot_cluster_metric` 
**default:** `ward`    
**oneOf:** `average,centroid,complete,median,single,ward,weighted`    

### `plot_dup_color` 
**default:** `#FFC633`    

### `plot_amp_color` 
**default:** `#FF6600`    

### `plot_del_color` 
**default:** `#33A0FF`    

### `plot_homodel_color` 
**default:** `#0033CC`    

### `plot_loh_color` 
**default:** `#0066FF`    

### `plot_snv_color` 
**default:** `#FF3300`    

### `plot_chros` 
**type:** array    
**items:** string    
**default:** `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22`    

### `plot_width` 
**description:**
    
* width of the plot image, in px     
* the plot area width is determined through
    - `plot_width - 2    
*plot_margins - plot_labelcol_width - plot_axislab_y_width - plot_dendrogram_width`    
**type:** integer    
**default:** `1024`    

### `plot_area_height` 
**description:**
height of the plot area (applies only to histogram plots)    
**type:** integer    
**default:** `100`    

### `plot_axis_y_max` 
**description:**
    
* frequency value the maximum of the Y-axis corresponds to     
* use this to e.g. spread values if a max. of less than 100 is expected    
**type:** integer    
**default:** `100`    

### `plot_samplestrip_height` 
**description:**
height of a single sample strip    
**type:** integer    
**default:** `12`    

### `plot_margins` 
**description:**
outer plot margins, in px    
**type:** integer    
**default:** `25`    

### `plot_labelcol_width` 
**description:**
    
* width of the space for left text labels (e.g. sample ids, collation
  labels)
    
* defaults to 0 when only one item    
**type:** integer    
**default:** `220`    

### `plot_axislab_y_width` 
**description:**
width of the space for histogram percentage markers    
**type:** integer    
**default:** `30`    

### `plot_dendrogram_width` 
**description:**
    
* width of the cluster tree     
* defaults to 0 when no clustering is being performed    
**type:** integer    
**default:** `50`    

### `plot_dendrogram_color` 
**description:**
color of the cluster tree stroke    
**default:** `#333333`    

### `plot_dendrogram_stroke` 
**description:**
thickness of the cluster tree stroke    
**type:** number    
**default:** `0.5`    

### `plot_chro_height` 
**description:**
height (well, width...) of the chromosomes in the ideogram strip    
**type:** integer    
**default:** `14`    

### `plot_region_gap_width` 
**type:** integer    
**default:** `3`    

### `plot_canvas_color` 
**description:**
color of the document background    
**default:** `#ffffff`    

### `plot_area_color` 
**description:**
color of the plot area background    
**default:** `#eef6ff`    

### `plot_area_opacity` 
**description:**
opacity of the plot background    
**type:** number    
**default:** `0.8`    

### `plot_heat_intensity` 
**description:**
factor for frequency heatmap value brightness    
**type:** number    
**default:** `1`    

### `plot_grid_stroke` 
**type:** integer    
**default:** `1`    

### `plot_grid_color` 
**description:**
color of grid lines    
**default:** `#c0e3ee`    

### `plot_grid_opacity` 
**type:** float    
**default:** `0.8`    

### `plot_font_color` 
**default:** `#000000`    

### `plot_font_size` 
**description:**
font size, in px    
**type:** integer    
**default:** `10`    

### `plot_title_font_size` 
**description:**
title font size, in px    
**type:** integer    
**default:** `16`    

### `plot_labelcol_font_size` 
**description:**
label font size (left column), in px    
**type:** integer    
**default:** `12`    

### `plot_label_y_font_size` 
**description:**
font size for Y-axis labels (percents ...)    
**type:** integer    
**default:** `8`    

### `plot_label_y_font_color` 
**description:**
font color for Y-axis labels (percents ...)    
**default:** `#666666`    

### `plot_label_y_values` 
**type:** array    
**items:** integer    
**default:** `25,50,75`    

### `plot_label_y_unit` 
**type:** string    
**default:** `%`    

### `plot_probe_y_factor` 
**description:**
relative y-scaling of the probes in array-/probeplots    
**type:** integer    
**default:** `1`    

### `plot_probe_label_y_values` 
**type:** array    
**items:** number    
**default:** `1,2,3,4,5,6,7,8,9`    

### `plot_probedot_size` 
**type:** integer    
**default:** `1`    

### `plot_probedot_opacity` 
**type:** integer    
**default:** `222`    

### `plot_region_labels` 
**description:**
    
* placeholder for markers / labels in the     
* format is `8:120000000-124000000:Region+of+Interest`     
* comma-concatenation for multiple values     
* label is optional    
**type:** array    

### `plot_regionlabel_color` 
**default:** `#ddceff`    

### `plot_gene_symbols` 
**description:**
    
* label a gene's position by its symbol (CDKN2A, MYC, ERBB2...)     
* comma-concatenation for multiple values    
**type:** array    

### `plot_cytoregion_labels` 
**description:**
    
* label a cytoband's position (8q24, 1p12p11, 17q...)     
* comma-concatenation for multiple values    
**type:** array    

### `plot_cytoregion_color` 
**default:** `#ffe3ee`    

### `plot_marker_font_color` 
**description:**
font color for gene and region markers    
**default:** `#dd3333`    

### `plot_marker_font_size` 
**type:** integer    
**default:** `10`    

### `plot_marker_label_padding` 
**description:**
text padding of markers versus background/box    
**type:** integer    
**default:** `4`    

### `plot_marker_lane_padding` 
**type:** integer    
**default:** `2`    

### `plot_footer_font_size` 
**type:** integer    
**default:** `10`    

### `plot_footer_font_color` 
**default:** `#999999`    
