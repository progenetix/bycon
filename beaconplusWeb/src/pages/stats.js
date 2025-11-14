import React from "react"
import DatasetStats from "./../components/DatasetStats"
import { Layout } from "./../site-specific/Layout"
import { DATASETDEFAULT } from "./../hooks/api"


export default function Page() {
  const title = `${DATASETDEFAULT} Data Content Overview`
  return (
    <Layout title={title} headline="">
      <DatasetStats dataset_id={DATASETDEFAULT} />
    </Layout>
  )
}
