import React from "react"
import DatasetStats from "./../components/DatasetStats"
import {Layout} from "./../site-specific/Layout"
import { withUrlQuery } from "../hooks/url-query"
import { urlRetrieveIds } from "./../hooks/api"

// http://beaconplus.org/stats/?datasetIds=progenetix&ageSplits=P0D,P1Y,P2Y,P18Y,P21Y,P40Y

const StatsPage = withUrlQuery(({ urlQuery }) => {
  var { datasetIds } = urlRetrieveIds(urlQuery)
  console.log(datasetIds)

  var ageSplits = urlQuery["ageSplits"]

  const title = `${datasetIds} Data Content Overview`
  const leadText = `This page shows some data statistics for the ${datasetIds}
dataset. Please allow for some loading time.`

  return (
    <Layout title={title} headline={title} leadPanelMarkdown={leadText}>
        <DatasetStats dataset_id={datasetIds} age_splits={ageSplits} filterUnknowns={true} />
    </Layout>
  )
})

export default StatsPage
