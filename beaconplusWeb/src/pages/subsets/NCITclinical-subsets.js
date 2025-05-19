import React from "react"
import { Layout } from "../../site-specific/Layout"
import { DATASETDEFAULT } from "../../hooks/api"
import SubsetsHierarchyLoader from  "../../components/SubsetsHierarchyLoader"

export default function NCITclinical_SubsetsPage() {
  return (
    <Layout title="TNM and Grade Subsets" headline="Cancers by TNM and Clinical Grade (NCIT)">
      <div className="content">
        <p>
          Where available cancer samples in Progenetix are mapped to with their
          standard clinical and histological parameters such as TNM classification
          or histological grade. 
        </p>
        <p>
          For each of the classes, aggregated date is available by
          clicking the code. Additionally, a selection of the corresponding
          samples can be initiated by clicking the sample number or selecting
          one or more classes through the checkboxes. Sample selection follows
          a hierarchical system in which samples
          matching the child terms of a selected class are included in the
          response.
        </p>
      </div>
      <SubsetsHierarchyLoader collationTypes="NCITtnm" datasetIds={DATASETDEFAULT}/>
      <SubsetsHierarchyLoader collationTypes="NCITgrade" datasetIds={DATASETDEFAULT}/>
      <SubsetsHierarchyLoader collationTypes="NCITstage" datasetIds={DATASETDEFAULT}/>
    </Layout>
  )
}
