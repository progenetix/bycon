import React from "react"
import { SubsetHistogram } from "../SVGloaders"
import {makeFilters, makePlotGeneSymbols} from "../../hooks/api"

export function SubsetsResults({query}) {
  const datasetIds = query.datasetIds.join(",")
  const filters = makeFilters(query).join(",")
  const plotGeneSymbols = makePlotGeneSymbols(query)
  const plotChros = query.plotChros ? query.plotChros.trim().split(",") : null

  return (
    <>
      <div className="subtitle ">
        <QuerySummary query={query} />
      </div>
      <SubsetHistogram
        datasetIds={datasetIds}
        id={filters}
        plotGeneSymbols={plotGeneSymbols}
        plotChros={plotChros}
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
