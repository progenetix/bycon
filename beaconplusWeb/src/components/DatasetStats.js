import React from "react"
import { AggregatedPlots } from "./AggregatedPlots"
import {
  basePath,
  useProgenetixApi,
} from "./../hooks/api"
import { Loader } from "./Loader"

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
        <AggregatedPlots
          summaryResults={data.response.collections[0].summaryResults}
          filterUnknowns={filterUnknowns}
        />
      )}
    </Loader>
  )
}
