import React from "react"
import { AggregatedPlots } from "./AggregatedPlots"
import {
  basePath,
  useProgenetixApi,
} from "./../hooks/api"
import { Loader } from "./Loader"
import Panel from "./Panel"

export default function FilterResultStats({dataset_id, ageSplits, followupSplits, filters, aggregationTerms, filterUnknowns}) {
  var summaryURL = `${basePath}beacon/biosamples?requestedGranularity=aggregated`
  var params = []

  if (dataset_id) {
    params.push(`datasetIds=${dataset_id}`)
  }
  if (followupSplits) {
    params.push(`followupSplits=${followupSplits}`)
  }
  if (aggregationTerms) {
    params.push(`aggregationTerms=${aggregationTerms}`)
  }
  if (ageSplits) {
    params.push(`ageSplits=${ageSplits}`)
  }
  if (filters) {
    params.push(`filters=${filters}`)
  } else {
    params.push(`testMode=true&testModeCount=1000`)
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
            <li>Analyses: {data.response.resultSets[0].info?.counts?.analyses}</li>
            <li>Biosamples: {data.response.resultSets[0].info?.counts?.biosamples}</li>
            <li>Individuals: {data.response.resultSets[0].info?.counts?.individuals}</li>
          </ul>
        </Panel>
        <Panel heading="Some Content Statistics">
          <AggregatedPlots
            summaryResults={data.response.resultSets[0].summaryResults}
            filterUnknowns={filterUnknowns}
          />
        </Panel>
        </>
      )}
    </Loader>
  )
}


