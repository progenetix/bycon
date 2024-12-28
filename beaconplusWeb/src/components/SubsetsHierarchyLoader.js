import { siteDataset, useFilterTreesByType } from "../hooks/api"
import { WithData } from "./Loader"
import React from "react"
import { keyBy } from "lodash"
import { buildTree, TreePanel } from "./classificationTree/TreePanel"


export default function SubsetsHierarchyLoader({ collationTypes, defaultTreeDepth }) {
  const collationsHierarchyReply = useFilterTreesByType({collationTypes})

  return (
    <WithData
      apiReply={collationsHierarchyReply}
      background
      render={(collationsHierarchyReply) => (
        <SubsetsResponse
          collationsHierarchies={collationsHierarchyReply.response.filteringTerms}
          defaultTreeDepth={defaultTreeDepth}
        />
      )}
    />
  )
}

function SubsetsResponse({ collationsHierarchies, defaultTreeDepth }) {
  const subsetById = keyBy(collationsHierarchies, "id")
  const { tree, size } = buildTree(collationsHierarchies, subsetById)

  return (
    <TreePanel
      datasetIds={siteDataset}
      subsetById={subsetById}
      tree={tree}
      size={size}
      defaultTreeDepth={defaultTreeDepth}
      sampleFilterScope="allTermsFilters"
    />
  )
}
