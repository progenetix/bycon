import React from "react"
import DatasetStats from "./../components/DatasetStats"
import { Layout } from "./../site-specific/Layout"
import { withUrlQuery } from "../hooks/url-query"
import { urlRetrieveIds } from "./../hooks/api"

const StatsPage = withUrlQuery(({ urlQuery }) => {
  var { id, datasetIds } = urlRetrieveIds(urlQuery)
  console.log(datasetIds)

  var ageSplits = urlQuery["ageSplits"]

  console.log(id)

  const title = `${datasetIds} Data Content Overview`
  return (
    <Layout title={title} headline={title}>
      <DatasetStats dataset_id={datasetIds} age_splits={ageSplits} />
    </Layout>
  )
})

export default StatsPage
