import React from "react"
import { EpmcLink } from "../helpersShared/linkHelpers"
import Table, { TooltipHeader, InfodotHeader } from "../Table"
import cn from "classnames"

export function PublicationTable({ publications }) {
  const publicationsCount = publications.length
  const sortType = React.useMemo(
    () => (rowA, rowB, id) => {
      const idA = getPublicationIdNumber(rowA.original[id])
      const idB = getPublicationIdNumber(rowB.original[id])
      return idA > idB ? 1 : idB > idA ? -1 : 0
    },
    []
  )
  const columns = React.useMemo(
    () => [
      {
        Header: `Publications (${publicationsCount})`,
        columns: [
          {
            Header: InfodotHeader(
              "id",
              "Publication id (PubMed) with link to details page"
            ),
            accessor: "id",
            sortType,
            Cell: function Cell(cellInfo) {
              return (
                <a href={`/publication/?id=${cellInfo.value}`}>
                  {cellInfo.value}
                </a>
              )
            }
          },
          {
            Header: "Publication",
            Cell: function Cell({ row: { original } }) {
              return (
                <>
                  <div>
                    {original.label} {original.journal}{" "}
                    <EpmcLink publicationId={original.id} />
                  </div>
                </>
              )
            }
          }
        ]
      },
      {
        Header: "Samples",
        columns: [
          {
            Header: TooltipHeader(
              "cCGH",
              "Chromosomal Comparative Genomic Hybridization samples in publication"
            ),
            accessor: "counts.ccgh",
            Cell: CountCell
          },
          {
            Header: TooltipHeader("aCGH", "Genomic Arrays in publication"),
            accessor: "counts.acgh",
            Cell: CountCell
          },
          {
            Header: TooltipHeader(
              "WES",
              "Whole Exome Sequencing experiments in publication"
            ),
            accessor: "counts.wes",
            Cell: CountCell
          },
          {
            Header: TooltipHeader(
              "WGS",
              "Whole Genome Sequencing experiments in publication"
            ),
            accessor: "counts.wgs",
            Cell: CountCell
          },
          {
            Header: TooltipHeader("pgx", "Samples in Progenetix"),
            accessor: "counts.progenetix",
            Cell: CountCell
          }
        ]
      },
      { accessor: "authors" },
      { accessor: "abstract" },
      { accessor: "title" }
    ],
    [publicationsCount, sortType]
  )
  return (
    <Table
      columns={columns}
      data={publications}
      pageSize={25}
      hiddenColumns={["authors", "abstract", "sortid", "title"]}
      sortBy={[{ id: "id", desc: true }]}
    />
  )
}

export function PublicationFewCountTable({ publications }) {
  const publicationsCount = publications.length
  const sortType = React.useMemo(
    () => (rowA, rowB, id) => {
      const idA = getPublicationIdNumber(rowA.original[id])
      const idB = getPublicationIdNumber(rowB.original[id])
      return idA > idB ? 1 : idB > idA ? -1 : 0
    },
    []
  )
  const columns = React.useMemo(
    () => [
      {
        Header: `Publications (${publicationsCount})`,
        columns: [
          {
            Header: InfodotHeader(
              "id",
              "Publication id (PubMed) with link to details page"
            ),
            accessor: "id",
            sortType,
            Cell: function Cell(cellInfo) {
              return (
                <a href={`/publication/?id=${cellInfo.value}`}>
                  {cellInfo.value}
                </a>
              )
            }
          },
          {
            Header: "Publication",
            Cell: function Cell({ row: { original } }) {
              return (
                <>
                  <div>
                    {original.label} {original.journal}{" "}
                    <EpmcLink publicationId={original.id} />
                  </div>
                </>
              )
            }
          }
        ]
      },
      {
        Header: "Samples",
        columns: [
          {
            Header: TooltipHeader(
              "Genomes",
              "Genome profiling experiments in publication"
            ),
            accessor: "counts.genomes",
            Cell: CountCell
          },
          {
            Header: TooltipHeader("pgx", "Samples in Progenetix"),
            accessor: "counts.progenetix",
            Cell: CountCell
          }
        ]
      },
      { accessor: "authors" },
      { accessor: "abstract" },
      { accessor: "title" }
    ],
    [publicationsCount, sortType]
  )
  return (
    <Table
      columns={columns}
      data={publications}
      pageSize={25}
      hiddenColumns={["authors", "abstract", "sortid", "title"]}
      sortBy={[{ id: "id", desc: true }]}
    />
  )
}


export function PublicationCompactTable({ publications }) {
  const publicationsCount = publications.length
  const sortType = React.useMemo(
    () => (rowA, rowB, id) => {
      const idA = getPublicationIdNumber(rowA.original[id])
      const idB = getPublicationIdNumber(rowB.original[id])
      return idA > idB ? 1 : idB > idA ? -1 : 0
    },
    []
  )

  const columns = React.useMemo(
    () => [
      {
        Header: `Publications (${publicationsCount})`,
        columns: [
          {
            Header: InfodotHeader(
              "id",
              "Publication id (PubMed) with link to details page"
            ),
            accessor: "id",
            sortType,
            Cell: function Cell(cellInfo) {
              return (
                <a href={`/publication/?id=${cellInfo.value}`}>
                  {cellInfo.value}
                </a>
              )
            }
          },
          {
            Header: "Publication",
            Cell: function Cell({ row: { original } }) {
              return (
                <>
                  <div>
                    {original.label} {original.journal}{" "}
                    <EpmcLink publicationId={original.id} />
                  </div>
                </>
              )
            }
          }
        ]
      }
    ],
    [publicationsCount, sortType]
  )
  return (
    <Table
      columns={columns}
      data={publications}
      pageSize={4}
      hiddenColumns={["sortid"]}
      sortBy={[{ id: "id", desc: true }]}
    />
  )
}

function CountCell({ value }) {
  return (
    <span className={cn(value === 0 && "has-text-grey-light")}>{value}</span>
  )
}

function getPublicationIdNumber(publicationId) {
  return +publicationId.substring(
    publicationId.indexOf(":") + 1,
    publicationId.length
  )
}


