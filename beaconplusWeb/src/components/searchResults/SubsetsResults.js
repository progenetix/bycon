// import { SITE_DEFAULTS } from "../../hooks/api"
import React from "react"
import { SubsetHistogram } from "../SVGloaders"
import {
  makeFilters
  // useSubsethistogram
} from "../../hooks/api"
// import { useContainerDimensions } from "../../hooks/containerDimensions"

export function SubsetsResults({query}) {
  console.log(query)
  console.log(query.datasetIds)
  const datasetIds = query.datasetIds.join(",")
  const filters = makeFilters(query).join(",")
  // const componentRef = useRef()
  // const { width } = useContainerDimensions(componentRef)
  // const size = width
  return (
    <>
      <div className="subtitle ">
        <QuerySummary query={query} />
      </div>
      <SubsetHistogram
        datasetIds={datasetIds} id={filters}
      />
    </>
  )
}


function QuerySummary({ query }) {
  const filters = makeFilters(query)
  return (
    <ul className="BeaconPlus__query-summary">
     {filters.length > 0 && (
        <li>
          <small>Filters: </small>
          {filters.join(", ")}
        </li>
      )}
{/*      {filters.length > 1 && (
        <li>
          <small>Filter Logic: </small>
          {query.filterLogic}
        </li>
      )}*/}
    </ul>
  )
}
