import React from "react"
import { AggregatedPlots } from "./AggregatedPlots"
import {
  basePath,
  useProgenetixApi,
} from "./../hooks/api"
import { Loader } from "./Loader"

export default function DatasetStats({dataset_id, age_splits, filterUnknowns}) {
  const summaryURL = `${basePath}beacon/datasets/${dataset_id}?ageSplits=${age_splits}`
  const { data, isLoading } = useProgenetixApi(summaryURL)
  return (
    <Loader isLoading={isLoading} background>
      {data && (
        <AggregatedPlots
          summaryResults={data.summaryResults}
          filterUnknowns={filterUnknowns}
        />
      )}
    </Loader>
  )
}
