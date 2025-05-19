import React from "react"
import { concat, merge } from "lodash"
import BiosamplesSearchPanel from "../components/searchForm/BiosamplesSearchPanel"
import parConfig from "../config/beaconSearchParameters.yaml"
import searchParLoc from "../site-specific/beaconSearchParameters.yaml"
import beaconQueryTypes from  "../config/beaconQueryTypes.yaml"
import { Layout } from "./../site-specific/Layout"
import baseSearchExamples from "../config/beaconSearchExamples.yaml"
import locSearchExamples from "../site-specific/beaconSearchExamples.yaml"
import { DATASETDEFAULT } from "../hooks/api"

const parametersConfig = merge(
  parConfig,
  searchParLoc
)

const searchExamples = concat(
  baseSearchExamples,
  locSearchExamples
)

if (!parametersConfig.parameters?.datasetIds?.defaultValue) {
  parametersConfig.parameters.datasetIds.defaultValue = [DATASETDEFAULT]
}

export function Page() {
  return (
    <Layout title="Search Samples" headline="">
      <BiosamplesSearchPanel
        parametersConfig={parametersConfig}
        beaconQueryTypes={beaconQueryTypes}
        requestTypeExamples={searchExamples}
        collapsed={false}
      />
    </Layout>
  )
}

export default Page
