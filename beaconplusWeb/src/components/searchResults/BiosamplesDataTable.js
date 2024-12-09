import { BIOKEYS } from "../../hooks/api"
import { ReferenceLink } from "../helpersShared/linkHelpers"
import React from "react"
import PropTypes from "prop-types"
import { WithData } from "../Loader"
import Table, { TooltipHeader } from "../Table"
import Link from "next/link"

export default function BiosamplesDataTable({ apiReply, datasetId }) {
  const columns = React.useMemo(
    () => [
      {
        Header: TooltipHeader(
          "Biosample Id",
          "Internal, stable (Progenetix) identifier for the biosample"
        ),
        accessor: "id",
        Cell: function Cell(cellInfo) {
          return (
            <Link
              href={`/biosample?id=${cellInfo.value}&datasetIds=${datasetId}`}
            >
              {cellInfo.value}
            </Link>
          )
        }
      },      
      {
        Header: TooltipHeader(
          "Dx Classifications",
          "Terms for biological classifications associated with the sample (e.g. diagnosis, histology, organ site)"
        ),
        accessor: "icdoMorphology.id",
        // eslint-disable-next-line react/display-name
        Cell: (cell) => (
          <div>
            {BIOKEYS.map(bioc => (
              <div key={bioc}>
                <Link
                href={`/subset/?id=${cell.row.original[bioc].id}&datasetIds=${datasetId}`}
                >
                  <a>{cell.row.original[bioc].id}</a>
                </Link>{" "}
                {cell.row.original[bioc].label}
              </div>
            ))}
          </div>
        )
      },
      {
        Header: TooltipHeader(
          "Identifiers",
          "Identifiers for technical metadata or external information, either specifically describing the sample or its context (e.g. publication, study, technical platform)"
        ),
        accessor: "externalReferences",
        Cell: ({ value: externalReferences }) =>
          externalReferences.map((externalReference, i) => (
            <div key={i}>
              {ReferenceLink(externalReference) ? (
                <Link href={ReferenceLink(externalReference)}>
                  <a>{externalReference.id}</a>
                </Link>
              ) : (
                externalReference.id
              )}{" "}
              {externalReference.description}
            </div>
          ))
      }
    ],
    [datasetId]
  )
  return (
    <WithData
      apiReply={apiReply}
      render={(response) => (
        <div>
          <Table columns={columns} data={response.response.resultSets[0].results} />
        </div>
      )}
    />
  )
}

BiosamplesDataTable.propTypes = {
  apiReply: PropTypes.object.isRequired
}
