import { Loader } from "../Loader"
import { DatasetResultBox } from "./DatasetResultBox"
import React from "react"
import { makeFilters } from "../../hooks/api"

export function BiosamplesResults({ response, isLoading, error, query }) {
  return (
    <>
      <div className="subtitle ">
        <QuerySummary query={query} />
      </div>
      <Loader isLoading={isLoading} hasError={error} colored background>
        {() => (
          <>
            <AlleleResponses
              biosampleResponseSets={response.response.resultSets}
              responseMeta={response.meta}
              query={query}
            />
          </>
        )}
      </Loader>
    </>
  )
}

function AlleleResponses({ biosampleResponseSets, responseMeta, query }) {
  if (biosampleResponseSets?.[0].resultsCount < 1) {
    return (
      <div className="notification">
        No results could be found for this query.
      </div>
    )
  }
  return biosampleResponseSets.map((r, i) => (
    <DatasetResultBox key={i} data={r} responseMeta={responseMeta} query={query} />
  ))
}

function QuerySummary({ query }) {
  const filters = makeFilters(query)
  return (
    <ul className="BeaconPlus__query-summary">
{/*      {query.assemblyId && (
        <li>
          <small>Assembly: </small>
          {query.assemblyId}
        </li>
      )}
*/}     
      {query.cytoBands && (
        <li>
          <small>Cytobands: </small>
          {query.cytoBands}
        </li>
      )}
      {query.variantQueryDigests && (
        <li>
          <small>Short Form: </small>
          {query.variantQueryDigests}
        </li>
      )}
      {query.geneId && (
        <li>
          <small>Gene: </small>
          {query.geneId}
        </li>
      )}
      {query.referenceName && (
        <li>
          <small>Chro: </small>
          {query.referenceName}
        </li>
      )}
      {query.start && (
        <li>
          <small>Start: </small>
          {query.start}
        </li>
      )}
      {query.end && (
        <li>
          <small>End: </small>
          {query.end}
        </li>
      )}
      {query.mateName && (
        <li>
          <small>Adjacent Chro: </small>
          {query.mateName}
        </li>
      )}
      {query.mateStart && (
        <li>
          <small>Adj. Start: </small>
          {query.mateStart}
        </li>
      )}
      {query.mateEnd && (
        <li>
          <small>Adj. End: </small>
          {query.mateEnd}
        </li>
      )}
      {query.variantType && (
        <li>
          <small>Type: </small>
          {query.variantType}
        </li>
      )}
      {query.variantMinLength && (
        <li>
          <small>Min. Length: </small>
          {query.variantMinLength}
        </li>
      )}
      {query.variantMaxLength && (
        <li>
          <small>Max. Length: </small>
          {query.variantMaxLength}
        </li>
      )}
      {query.referenceBases && (
        <li>
          <small>Ref. Base(s): </small>
          {query.referenceBases}
        </li>
      )}
      {query.alternateBases && (
        <li>
          <small>Alt. Base(s): </small>
          {query.alternateBases}
        </li>
      )}
      {filters.length > 0 && (
        <li>
          <small>Filters: </small>
          {filters.join(", ")}
        </li>
      )}
      {filters.length > 1 && (
        <li>
          <small>Filter Logic: </small>
          {query.filterLogic}
        </li>
      )}
    </ul>
  )
}
