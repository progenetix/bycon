import React from "react"
import { SubsetHistogram } from "../SVGloaders"
import {makeFilters, makePlotGeneSymbols} from "../../hooks/api"

export function SubsetsResults({query}) {
  const datasetIds = query.datasetIds.join(",")
  const filters = makeFilters(query).join(",")
  const plotType = query.plotType ? query.plotType : "histoplot"
  const plotGeneSymbols = makePlotGeneSymbols(query)
  const plotChros = query.plotChros ? query.plotChros.trim().split(",") : null
  const plotParsString = query.plotParsString ? query.plotParsString.trim().replace(/:/g, "=").split(";").join("::") : null

  console.log(plotParsString)

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
        plotParsString={plotParsString}
        plotType={plotType}
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
    </ul>
  )
}
