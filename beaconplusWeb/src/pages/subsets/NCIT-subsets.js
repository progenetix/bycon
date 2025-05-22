import React from "react"
import { Layout } from "../../site-specific/Layout"
import { DATASETDEFAULT } from "../../hooks/api"
import SubsetsHierarchyLoader from  "../../components/SubsetsHierarchyLoader"

export default function Page() {
  return (
    <Layout title="Subsets" headline="Cancer Types by National Cancer Institute NCIt Code">
      <div className="content">
        <p>
          The cancer samples in Progenetix are mapped to several classification
          systems. For each of the classes, aggregated date is available by
          clicking the code. Additionally, a selection of the corresponding
          samples can be initiated by clicking the sample number or selecting
          one or more classes through the checkboxes.
        </p>
        <p>
          Sample selection follows a hierarchical system in which samples
          matching the child terms of a selected class are included in the
          response.
        </p>
      </div>
      <SubsetsHierarchyLoader collationTypes="NCIT" datasetIds={DATASETDEFAULT}/>
    </Layout>
  )
}
