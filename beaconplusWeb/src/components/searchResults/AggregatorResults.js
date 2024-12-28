import { Loader } from "../Loader"
import { ExternalLink } from "../helpersShared/linkHelpers"
// import { QuerySummary } from "../QuerySummary"
// import { DatasetResultBox } from "./DatasetResultBox"
import React from "react"

export function AggregatorResults({ response, isLoading, error, query }) {
  return (
    <>

{/*      <div className="subtitle ">
        <QuerySummary query={query} />
      </div>
*/}
      <Loader isLoading={isLoading} hasError={error} colored background>
        {() => (
          <>
            <AggregatorResponses
              aggregatorResponseSets={response.response.responseSets}
              query={query}
            />
          </>
        )}
      </Loader>
    </>
  )
}

function AggregatorResponses({ aggregatorResponseSets }) {
  return aggregatorResponseSets.map((r, i) => (
    <AggregatorResultBox key={i} data={r} />
  ))
}

function AggregatorResultBox({data: responseSet}) {
  const {
    id,
    apiVersion,
    datasetId,
    exists,
    error,
    info
  } = responseSet

  const logoStyle = {
    float: "right",
    maxWidth: "120px",
    border: "0px",
    margin: "-50px 0px 0px 0px"
  }

  return (
    <div className="box">
      <h2 className="subtitle has-text-dark">{id}{datasetId && <span> {"("}{datasetId}{")"}</span>}</h2>
      {info.logoUrl &&
        <img
          src={info.logoUrl}
          style={logoStyle}
        />
      }
      <div>
        <b>API Version: </b>
          {apiVersion}
      </div>
      <div>
        <b>Variant: </b>
          <span style={exists ? {"font-weight": "bold", color: "green"} : {color: "red"}}>
            {exists.toString()}
          </span>
      </div>
      <div>
        <b>Query: </b>
          <ExternalLink
            label={info.queryUrl.replace(/https?:\/\//, "")}
            href={info.queryUrl}
          />
      </div>
      {info.responseTime &&
        <div>
          <b>Response Time: </b>
          {info.responseTime}
        </div>
      }
      {info.welcomeUrl &&
        <div>
          <b>Info: </b>
          <ExternalLink
            label="web page"
            href={info.welcomeUrl}
          />
        </div>
      }
      {error && (
        <div>
          <b>Error: </b>
            {error}
        </div>
      )}
    </div>
  )

}

