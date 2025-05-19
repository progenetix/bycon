import React from "react"
import { useFilterTreesByType } from "../hooks/api"
import { WithData } from "./Loader"
import { keyBy } from "lodash"
import { buildTree, TreePanel } from "./classificationTree/TreePanel"

export default function SubsetsHierarchyLoader({ collationTypes, datasetIds, defaultTreeDepth }) {
  const collationsHierarchyReply = useFilterTreesByType({
    datasetIds,
    collationTypes
  })

  return (
    <WithData
      apiReply={collationsHierarchyReply}
      background
      render={(collationsHierarchyReply) => (
        <SubsetsResponse
          collationsHierarchies={collationsHierarchyReply.response.filteringTerms}
          datasetIds={datasetIds}
          defaultTreeDepth={defaultTreeDepth}
        />
      )}
    />
  )
}

function SubsetsResponse({ collationsHierarchies, datasetIds, defaultTreeDepth }) {
  const subsetById = keyBy(collationsHierarchies, "id")
  const { tree, size } = buildTree(collationsHierarchies, subsetById)

  return (
    <TreePanel
      datasetIds={datasetIds}
      subsetById={subsetById}
      tree={tree}
      size={size}
      defaultTreeDepth={defaultTreeDepth}
      sampleFilterScope="allTermsFilters"
    />
  )
}
