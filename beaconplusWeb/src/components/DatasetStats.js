import React from "react"
import { AggregatedPlots } from "./AggregatedPlots"
import {
  basePath,
  useProgenetixApi,
} from "./../hooks/api"

export default function DatasetStats({dataset_id}) {
  const summaryURL = `${basePath}beacon/datasets/${dataset_id}`
  const summaryReply = useProgenetixApi(summaryURL)
  return (
    <AggregatedPlots
      summaryResults={summaryReply?.data?.summaryResults}
    />
  )
}
