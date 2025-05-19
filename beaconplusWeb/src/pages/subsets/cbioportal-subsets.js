import React from "react"
import { Layout } from "../../site-specific/Layout"
import { DATASETDEFAULT } from "../../hooks/api"
import Panel from "../../components/Panel"
import SubsetsHierarchyLoader from  "../../components/SubsetsHierarchyLoader"

export default function Page() {
  return (
    <Layout title="Subsets" headline="cBioPortal Studies">
      <div className="content">
        <p>
          This page represents samples from different cancer studies derived from cBioPortal.
        </p>
      </div>
      <Panel heading="cBioPortal Studies">
        <SubsetsHierarchyLoader collationTypes="cbioportal" datasetIds={DATASETDEFAULT} />
      </Panel>
    </Layout>
  )
}

