import React from "react"
import { SummaryPlots } from "./summaries/SummaryPlots"
import {
  basePath,
  useProgenetixApi,
} from "./../hooks/api"
import { Loader } from "./Loader"
import Panel from "./Panel"

export default function FilterResultStats({dataset_id, ageSplits, followupSplits, filters, aggregators, filterUnknowns}) {
  var summaryURL = `${basePath}beacon/biosamples?requestedGranularity=aggregated`
  var params = []

  if (dataset_id) {
    params.push(`datasetIds=${dataset_id}`)
  }
  if (followupSplits) {
    params.push(`followupSplits=${followupSplits}`)
  }
  if (aggregators) {
    params.push(`aggregators=${aggregators}`)
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
          <SummaryPlots
            resultsAggregation={data.response.resultSets[0].resultsAggregation}
            filterUnknowns={filterUnknowns}
          />
        </Panel>
        </>
      )}
    </Loader>
  )
}


