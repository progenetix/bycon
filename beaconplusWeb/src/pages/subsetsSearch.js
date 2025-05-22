import React from "react"
import { merge } from "lodash"
import SubsetsSearchPanel from "../components/subsetsForm/SubsetsSearchPanel"
import parConfig from "../config/beaconSearchParameters.yaml"
import subsetsParMods from "../config/subsetsSearchParametersMods.yaml"
import { Layout } from "./../site-specific/Layout"
import requestTypeExamples from "../site-specific/searchExamples.yaml"

const parametersConfig = merge(
  parConfig,
  subsetsParMods
)

export default function Page() {
  return (
    <Layout title="Search and Compare Subsets" headline="">
      <SubsetsSearchPanel
        parametersConfig={parametersConfig}
        requestTypeExamples={requestTypeExamples}
        collapsed={false}
      />
    </Layout>
  )
}
