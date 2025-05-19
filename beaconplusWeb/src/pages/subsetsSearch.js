import React from "react"
import { concat, merge } from "lodash"
import SubsetsSearchPanel from "../components/searchForm/SubsetsSearchPanel"
import parConfig from "../config/beaconSearchParameters.yaml"
import subsetsParMods from "../config/subsetsSearchParametersMods.yaml"
import subsetsParLoc from "../site-specific/subsetsSearchParameters.yaml"
import { Layout } from "../site-specific/Layout"
import baseSubsetsExamples from "../config/subsetsExamples.yaml"
import locSubsetsExamples from "../site-specific/subsetsExamples.yaml"
import { DATASETDEFAULT } from "../hooks/api"

const parametersConfig = merge(
  parConfig,
  subsetsParMods,
  subsetsParLoc
)

const subsetsExamples = concat(
  baseSubsetsExamples,
  locSubsetsExamples
)

if (!parametersConfig.parameters?.datasetIds?.defaultValue) {
  parametersConfig.parameters.datasetIds.defaultValue = [DATASETDEFAULT]
}

export function Page() {
  return (
    <Layout title="Search and Compare Subsets" headline="">
      <SubsetsSearchPanel
        parametersConfig={parametersConfig}
        requestTypeExamples={subsetsExamples}
        collapsed={false}
      />
    </Layout>
  )
}

export default Page
