import React from "react"
import { AggregatedPlots } from "./AggregatedPlots"
import {
  basePath,
  useProgenetixApi,
} from "./../hooks/api"
import { Loader } from "./Loader"
import Panel from "./Panel"

export default function DatasetStats({dataset_id, age_splits, followup_splits, filterUnknowns}) {
  var summaryURL = `${basePath}beacon/datasets/${dataset_id}?requestedGranularity=aggregated`
  var params = []

  if (followup_splits) {
    params.push(`followupSplits=${followup_splits}`)
  }
  if (age_splits) {
    params.push(`ageSplits=${age_splits}`)
  }
  if (params.length > 0) {
    summaryURL += `&${params.join("&")}`
  }

  const { data, isLoading } = useProgenetixApi(summaryURL)
  return (
    <Loader isLoading={isLoading} background>
      {data && (
        <>
        <Panel heading="Dataset Summary">
          <ul>
            <li>Variants: {data.response.collections[0].counts.genomicVariant}</li>
            <li>Analyses: {data.response.collections[0].counts.analysis}</li>
            <li>Biosamples: {data.response.collections[0].counts.biosample}</li>
            <li>Individuals: {data.response.collections[0].counts.individual}</li>
          </ul>
        </Panel>
        <Panel heading="Some Content Statistics">
          <AggregatedPlots
            summaryResults={data.response.collections[0].summaryResults}
            filterUnknowns={filterUnknowns}
          />
        </Panel>
        </>
      )}
    </Loader>
  )
}


