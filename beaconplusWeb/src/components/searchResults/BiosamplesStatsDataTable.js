import React from "react"
import PropTypes from "prop-types"
import Table, { InfodotHeader } from "../Table"
import _ from "lodash"
import { BIOKEYS, useCollationsById } from "../../hooks/api"
import { WithData } from "../Loader"

export default function BiosamplesStatsDataTable({
  biosamplesResponse,
  variantCount,
  datasetId
}) {
  const columns = React.useMemo(
    () =>
      [
        {
          Header: InfodotHeader(
            "Matched Subset Codes",
            "Coded diagnoses or other biomedical classifications which are represented in the matched samples."
          ),
          accessor: "id",
          Cell: function Cell({ value, row: { original } }) {
            return (
              <span>
              
                <a
                  href={`/subset/?id=${original.id}&datasetIds=${datasetId}`}
                >
                  {value}
                </a>
              </span>
            )
          }
        },
        {
          Header: InfodotHeader(
            "Subset Samples",
            "Overall number of samples in the database which match the given subset code."
          ),
          accessor: "samples"
        },
        {
          Header: InfodotHeader(
            "Matched Samples",
            "Number of matched samples with the given code."
          ),
          accessor: "count"
        },
        variantCount > 0
          ? [
              {
                Header: InfodotHeader(
                  "Subset Match Frequencies",
                  "Proportion of matched samples with the given code, relativ to the overall number of samples with the code. Please be aware that the frequence e.g. does not correspond to e.g. the frequency in a pre-selected cohort but to the whole dataset."
                ),
                accessor: "frequency",
                Cell: function Cell({ value }) {
                  return (
                    <>
                      <span
                        style={{
                          width: `${value * 100}%`,
                          height: `80%`,
                          position: "absolute",
                          left: 0,
                          backgroundColor: "#d8d8d8"
                        }}
                      />
                      <span
                        style={{
                          position: "absolute",
                          paddingLeft: "1rem"
                        }}
                      >
                        {value}
                      </span>
                    </>
                  )
                }
              }
            ]
          : []
      ].flat(),
    [variantCount, datasetId]
  )

  const allSubsetsReply = useCollationsById({ datasetIds: datasetId })
  return (
    <WithData
      apiReply={allSubsetsReply}
      background
      render={(allSubsetsResponse) => {
        const subsets = makeSubsetsData(
          biosamplesResponse.response.resultSets[0].results,
          allSubsetsResponse.results
        )
        return <Table columns={columns} data={subsets} pageSize={20} />
      }}
    />
  )
}

function getFrequency(v, allSubsetsById, k) {
  const allSubsetsCount = allSubsetsById[k]?.count ?? -1
  if (allSubsetsCount <= 0) return ""
  return (v / allSubsetsCount).toFixed(3).toString()
}

export function makeSubsetsData(biosamplesResults, allSubsetsById) {
  const ids = biosamplesResults
    .flatMap((sample) => BIOKEYS.map(bioc => (sample[bioc])))
    .filter(a => a)
    .map(function (a) {
      return a.id     
    })
  const subsetCounts = _.countBy(ids)
  const subsets = Object.entries(subsetCounts).map(([k, v]) => ({
    id: k,
    count: v,
    frequency: getFrequency(v, allSubsetsById, k),
    samples: allSubsetsById[k]?.count
  }))

  return _.sortBy(subsets, "frequency").reverse()
}

BiosamplesStatsDataTable.propTypes = {
  biosamplesResponse: PropTypes.object.isRequired
}
