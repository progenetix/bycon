import React from "react"
import { merge } from "lodash"
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

const searchExamples = merge(
  baseSearchExamples,
  locSearchExamples
)

if (!parametersConfig.parameters?.datasetIds?.defaultValue) {
  parametersConfig.parameters.datasetIds.defaultValue = [DATASETDEFAULT]
}

const leadText = `This search form shows parameter combinations and examples for
different Beacon search patterns. Please be aware that search types and examples
are _independent_ of each other, so not all combinations are automatically adjusted.

Additionally, the search options here might extend the latest stable version of
the Beacon API in a sense of "implementation driven development" but are supported
through this version of the [\`bycon\`](https://bycon.progenetix.org) library.`

export function Page() {
  return (
    <Layout title="Search Samples" headline="Beacon Search Demonstrator" leadPanelMarkdown={leadText}>
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
