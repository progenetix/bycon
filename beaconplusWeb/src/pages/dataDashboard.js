import React from "react"
import DatasetStats from "./../components/DatasetStats"
import Panel from "../components/Panel"
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
dataset. Current modification options are through URL parameters for (with examples):

* "datasetIds=progenetix" (or other supported dataset)
* "ageSplits=P0D,P1Y,P2Y,P18Y,P21Y,P40Y" ... as example for age binning
* "followupTime=P0D,P1D,P6M,P1Y,P5Y,P10Y" ... as example for followup binning

Please allow for some loading time.`

  return (
    <Layout title={title} headline={title} leadPanelMarkdown={leadText}>
      <Panel>
        <DatasetStats dataset_id={datasetIds} age_splits={ageSplits} filterUnknowns={true} />
      </Panel>
    </Layout>
  )
})

export default StatsPage
