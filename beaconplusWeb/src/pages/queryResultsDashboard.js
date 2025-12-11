import React from "react"
import FilterResultStats from "./../components/FilterResultStats"
import {Layout} from "./../site-specific/Layout"
import { withUrlQuery } from "../hooks/url-query"
import { basePath, urlRetrieveIds } from "./../hooks/api"

// http://beaconplus.org/stats/?datasetIds=progenetix&ageSplits=P0D,P1Y,P2Y,P18Y,P21Y,P40Y

const QueryStatsPage = withUrlQuery(({ urlQuery }) => {
  var { datasetIds } = urlRetrieveIds(urlQuery)
  console.log(datasetIds)

  var ageSplits = urlQuery["ageSplits"]
  var followupSplits = urlQuery["followupSplits"]
  var filters = urlQuery["filters"]
  var aggregationTerms = urlQuery["aggregationTerms"]

  const title = `${datasetIds} Data Content Overview`
  const leadText = `This page shows some data statistics for the ${datasetIds}
dataset. Current modification options are through URL parameters for (with examples):

* ${"`datasetIds=progenetix`"} (or other supported dataset)
* ${"`ageSplits=P0D,P1Y,P2Y,P18Y,P21Y,P40Y`"} ... as example for age binning
* ${"`followupTime=P0D,P1D,P6M,P1Y,P5Y,P10Y`"} ... as example for followup binning
* ${"`filters=pgx:cohort-TCGAcancers`"} ... as example for a custom filter
* ${"`aggregationTerms=ageAtDiagnosisBySex`"} ... for limited aggregations

Example URL would be:

* TCGA samples in Progenetix for age groups, split by sex
    - ${"`"}${basePath}queryResultsDashboard/?datasetIds=progenetix&filters=pgx:cohort-TCGAcancers&aggregationTerms=ageAtDiagnosisBySex${"`"}
* Brain cancers in Progenetix by some aggregation types (see the bimodal age distribution)...
    - ${"`"}${basePath}queryResultsDashboard/?datasetIds=progenetix&filters=NCIT:C3268&aggregationTerms=ageAtDiagnosisBySex,diseaseBySex,followupTime${"`"}
Please allow for some loading time.`

  return (
    <Layout title={title} headline={title} leadPanelMarkdown={leadText}>
        <FilterResultStats 
            dataset_id={datasetIds}
            ageSplits={ageSplits}
            followupSplits={followupSplits}
            filters={filters}
            aggregationTerms={aggregationTerms}
            filterUnknowns={true}
        />
    </Layout>
  )
})

export default QueryStatsPage
