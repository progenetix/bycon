import React from "react"
import { SummaryPlots } from "./SummaryPlots"
import {
  basePath,
  useProgenetixApi,
} from "./../hooks/api"
import { Loader } from "./Loader"
import Panel from "./Panel"

export default function DatasetStats({dataset_id, ageSplits, followupSplits, aggregationTerms, filterUnknowns}) {
  var summaryURL = `${basePath}beacon/datasets/${dataset_id}?requestedGranularity=aggregated`
  var params = []

  if (followupSplits) {
    params.push(`followupSplits=${followupSplits}`)
  }
  if (ageSplits) {
    params.push(`ageSplits=${ageSplits}`)
  }
  if (aggregationTerms) {
    params.push(`aggregationTerms=${aggregationTerms}`)
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
          <SummaryPlots
            summaryResults={data.response.collections[0].summaryResults}
            filterUnknowns={filterUnknowns}
          />
        </Panel>
        </>
      )}
    </Loader>
  )
}


