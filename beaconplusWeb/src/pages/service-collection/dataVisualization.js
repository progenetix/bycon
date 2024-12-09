import { withUrlQuery } from "../../hooks/url-query"
import { Layout } from "../../site-specific/Layout"
import React, { useRef, useState } from "react"
// import { GeneLabelOptions } from "../../components/formShared/GenespanUtilities"
import { useForm } from "react-hook-form"
// import SelectField from "../../components/formShared/SelectField"
import InputField from "../../components/formShared/InputField"
import cn from "classnames"
import { useDataVisualization, useExtendedSWR } from "../../hooks/api"
import { WithData } from "../../components/Loader"
import { useContainerDimensions } from "../../hooks/containerDimensions"
// import { useAsyncSelect } from "../../hooks/asyncSelect"

import SVGloader from "../../components/SVGloaders"
import { svgFetcher } from "../../hooks/fetcher"

const sampleMaxNo = 1000

const HANDOVER_IDS = {
  histoplot: "pgx:HO.histoplot",
  samplesplot: "pgx:HO.samplesplot"
}

const DataVisualizationPage = withUrlQuery(({ urlQuery }) => {
  const { datasetIds, accessid, fileId, skip, limit, sampleCount } = urlQuery
  const componentRef = useRef()
  const { width } = useContainerDimensions(componentRef)
  return (
    <Layout
      title="Data visualization"
      headline={`Data visualization (${sampleCount} ${datasetIds} samples)`}
    >
      {!accessid && !fileId ? (
        <NoResults />
      ) : (
        <div ref={componentRef}>
          {sampleCount > sampleMaxNo && (
            <p>
              Please limit the visualization to about {sampleMaxNo} samples; otherwise this might time out...
            </p>
          )}
          {width > 0 && (
            <DataVisualizationPanel
              datasetIds={datasetIds}
              accessid={accessid}
              fileId={fileId}
              skip={skip}
              limit={limit}
              width={width}
            />
          )}
        </div>
      )}
    </Layout>
  )
})

export default DataVisualizationPage

function NoResults() {
  return (
    <div className="notification is-size-5 content">
      This page will only show content if called with a specific <i>accessid</i>
      or <i>fileId</i> .
      <br />
      Please start over from the Search Samples page or{" "}
      <a href="/service-collection/uploader">upload a file</a>.
    </div>
  )
}

// TODO: rewrite to use simple plot endpoint calls instead of the biosamples + handovers construct...
function DataVisualizationPanel({ datasetIds, accessid, fileId, skip, limit, width }) {
  const [formValues, setFormValues] = useState({})
  const dataResult = useDataVisualization({
    "datasetIds": datasetIds,
    "accessid": accessid,
    "fileId": fileId,
    "skip": skip,
    "limit": limit,
    "requestedGranularity": "count",
    "includeHandovers": "true",
    ...formValues
  })
  const onSubmit = (values) => {
    setFormValues(values)
    dataResult.mutate(null)
  }
  return (
    <div>
      <div className="columns">
        <div className="mb-6 column">
          <DataVisualizationForm
            isQuerying={false}
            limit={limit}
            onSubmit={onSubmit}
          />
        </div>
      </div>
      <WithData
        background
        apiReply={dataResult}
        render={(data) =>
          <ResultPanel
            formValues={formValues}
            response={data}
            width={width}
            datasetIds={datasetIds}
          />}
      />
    </div>
  )
}

function DataVisualizationForm({ isQuerying, limit, onSubmit }) {
  const defaultValues = {
    "plotRegionLabels": null,
    "plotGeneSymbols": null
  }
  const { register, handleSubmit, errors } = useForm({ defaultValues })
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="columns">
        <div className="column">
          <InputField
            name="plotChros"
            label="Chromosomes"
            infoText="The chromosomes to be included in the plot, in the order they should appear. The values should just be the comma-separated chromosome numbers (e.g. '1,3,19,X' - unquoted, no spaces). The default is chr 1-22."
            errors={errors}
            register={register}
          />
        </div>
{/*
        <div className="column">
          <SelectField
            name="group_by"
            register={register}
            label="Plot Grouping"
            options={groupByOptions}
            control={control}
            infoText="A selection here will produce separate histograms for samples aggregated for the given scope, e.g. all samples from the same publication or diagnostic code. This requires that samples contain several different types for the selected aggregation scope."
            errors={errors}
          />
        </div>

        <div className="column">
          <InputField
            name="min_group_no"
            label="Min. Samples per Group"
            errors={errors}
            register={register}
            infoText="Minimum number of samples for aggregated groups."
            defaultValue="2"
          />
        </div>
*/}
{/*
        <div className="column">
          <InputField
            name="bin_match_min"
            label="Min. Interval Fraction"
            errors={errors}
            register={register}
            infoText="CNV frequencies are calculated for genomic bins, normally for a 1Mb size. The minimal interval fraction value allows to require a minimum amount of overlap of a CNV with these bins; a value of 0.5 will only use CNVs which overlap an interval by at least 50% for histogram display and sample clustering."
            defaultValue="0.00001"
          />
        </div>
*/}        
      </div>
      <div className="columns">
        <div className="column">
          <InputField
            name="plotLabelcolWidth"
            label="Left Labels Width (px)"
            errors={errors}
            register={register}
          />
        </div>
        <div className="column">
          <InputField
            name="plotSamplestripHeight"
            label="Sample Line Height (px)"
            errors={errors}
            register={register}
            defaultValue="12"
          />
        </div>
{/*
      </div>
      <div className="columns">
*/}      
        <div className="column">
          <InputField
            name="plotAreaHeight"
            label="Histogram Height (px)"
            errors={errors}
            register={register}
            infoText="Height of the histogram plot area, in pixels."
          />
        </div>
        <div className="column">
          <InputField
            name="plot_axis_y_max"
            label="Histogram Max. Scale (%)"
            errors={errors}
            register={register}
            infoText="Maximum CNV frequency percentage in the histogram."
          />
        </div>
        <div className="column">
          <InputField
            name="plotDendrogramWidth"
            label="Cluster Tree Width (px)"
            errors={errors}
            register={register}
            infoText="Width of the tree for sample and group clustering, in pixels."
          />
        </div>
      </div>
      <div className="columns">
        <div className="column">
{/*          <GeneSpanSelector
            errors={errors}
            register={register}
            control={control}
            infoText="Select one or more genes to be highlighted on the plots."
          />
*/}  
          <InputField
            name="plotGeneSymbols"
            label="Gene Symbols"
            errors={errors}
            register={register}
            infoText="Label gene positions by their symbols (e.g. MYC, TP53)"
          />
        </div>
        <div className="column">
          <InputField
            name="plotRegionLabels"
            label="Free Labels"
            errors={errors}
            register={register}
            infoText="Add one or more comma-concatenated custom labels to the plot in the form of '7:10000000-20000000:MyLabel,18:8500000-8600000:Strange Spot'"
            defaultValue=""
          />
        </div>
        <div className="column">
          <InputField
            name="limit"
            label="Limit"
            errors={errors}
            register={register}
            infoText="Maximum number of samples processed"
            defaultValue={limit}
          />
        </div>
      </div>
      <div className="field mt-5">
        <div className="control">
          <button
            type="submit"
            className={cn("button", "is-primary", {
              "is-loading": isQuerying
            })}
          >
            Plot Data
          </button>
        </div>
      </div>
    </form>
  )
}

function ResultPanel({ formValues, response, width, datasetIds }) {
  const resultsHandovers = response.response.resultSets[0].resultsHandovers
  const handoverById = (givenId) =>
    resultsHandovers.find(({ handoverType: { id } }) => id === givenId)

  const mapped = [`plot_width=${width}`];
  Object.entries(formValues).forEach(([k, v]) => {
    if (v != null && v != "") {
      mapped.push(`${k}=${v}`);
    }
  });

  const histoplotUrl = handoverById(HANDOVER_IDS.histoplot).url + "&plotPars=" + mapped.join('::') + "&datasetIds=" + datasetIds
  const samplesplotUrl = handoverById(HANDOVER_IDS.samplesplot).url + "&plotPars=" + mapped.join('::') + "&datasetIds=" + datasetIds

  return (
    <div>
      <div>
        <SVGloader apiReply={ useExtendedSWR(histoplotUrl, svgFetcher) } />
        <a href={histoplotUrl} target="_blank" rel="noreferrer">
          Open Histogram
        </a>
      </div>
      <div>
        <SVGloader apiReply={ useExtendedSWR(samplesplotUrl, svgFetcher) } />
        <a href={samplesplotUrl} target="_blank" rel="noreferrer">
          Open Sample Plot
        </a>
      </div>
    </div>
  )
}

// const groupByOptions = [
//   { value: "", label: "No Grouping" },
//   { value: "NCIT", label: "NCIT Neoplasm Code" },
//   { value: "icdom", label: "ICD-O Morphology Code" },
//   { value: "icdot", label: "ICD Topography Code" },
//   { value: "UBERON", label: "UBERON Anatomy Concepts" },
//   { value: "TNM", label: "NCIT TNM Finding" },
//   // { value: "NCITgrade", label: "NCIT Disease Grade" },
//   // { value: "NCITstage", label: "NCIT Disease Stage" },
//   // { value: "EFOfus", label: "followup status" },
//   { value: "pubmed", label: "Publication (PubMed ID)" },
//   // { value: "geo:GSE", label: "GEO Series ID" },
//   // { value: "geo:GPL", label: "GEO Platform ID" },
//   {
//     value: "cellosaurus",
//     label: "Cellosaurus Cell line ID"
//   }
// ]

// function GeneSpanSelector({ control, errors, register }) {
//   const { inputValue, onInputChange } = useAsyncSelect()
//   const { options, isLoading } = GeneLabelOptions(inputValue)
//   return (
//     <SelectField
//       name="plotGeneSymbols"
//       label="Select Gene Label"
//       isLoading={isLoading && !!inputValue}
//       options={options}
//       onInputChange={onInputChange}
//       control={control}
//       errors={errors}
//       register={register}
//       isMulti
//     />
//   )
// }
