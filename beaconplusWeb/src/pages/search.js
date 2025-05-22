import React from "react"
import BiosamplesSearchPanel from "../components/searchForm/BiosamplesSearchPanel"
import parametersConfig from "../config/beaconSearchParameters.yaml"
import beaconQueryTypes from  "../config/beaconQueryTypes.yaml"
import { Layout } from "./../site-specific/Layout"
import requestTypeExamples from "../site-specific/searchExamples.yaml"

export default function Page() {
  return (
    <Layout title="Search Samples" headline="">
      <BiosamplesSearchPanel
        parametersConfig={parametersConfig}
        beaconQueryTypes={beaconQueryTypes}
        requestTypeExamples={requestTypeExamples}
        collapsed={false}
      />
    </Layout>
  )
}
