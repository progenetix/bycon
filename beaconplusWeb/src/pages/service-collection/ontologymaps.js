import React, { useEffect, useState } from "react"
import { Infodot } from "../../components/Infodot"
import { Layout } from "../../site-specific/Layout"
import {
  ontologymapsBaseUrl,
  ontologymapsPrefUrl
} from "../../hooks/api"
import CustomSelect from "../../components/Select"
import { Loader } from "../../components/Loader"
import { withUrlQuery } from "../../hooks/url-query"
import {
  CodeGroups,
  useOntologymaps,
  useGetFilteredOptions
} from "../../components/OntomapsComponents"

const filterPrecision = "start"
const prefixes = "NCIT,pgx:icdom,pgx:icdot"
const apiAllMapsURL = `${ontologymapsBaseUrl}filters=${prefixes}`

export default function OntologymapsPage() {
  return (
    <Layout title="Ontologymaps" headline="Services: Ontologymaps (NCIt)">
      <div className="content">
        <img
          src="/img/ncit-logo-320x80.jpg"
          className="Layout__img__topright Layout__img__width-160"
        />
        <p>
          The <strong>ontologymaps</strong> service provides equivalency mapping
          between ICD-O and other classification systems, notably NCIt and
          UBERON. It makes use of the sample-level mappings for NCIT and ICD-O 3
          codes developed for the individual samples in the Progenetix
          collection.
        </p>
        <h4>NCIT and ICD-O 3</h4>
        <p>
          While NCIT treats diseases as{" "}
          <span className="span-blue">histologic</span> and{" "}
          <span className="span-red">topographic</span> described entities (e.g.{" "}
          <span className="span-purple">NCIT:C7700</span>:{" "}
          <span className="span-red">Ovarian</span>{" "}
          <span className="span-blue">adenocarcinoma</span>), these two
          components are represented separately in ICD-O, through the{" "}
          <span className="span-blue">Morphology</span> and{" "}
          <span className="span-red">Topography</span> coding arms (e.g. here{" "}
          <span className="span-blue">8140/3</span> +{" "}
          <span className="span-red">C56.9</span>).
        </p>
        <p>
          More documentation with focus on the API functionality can be found on
          the documentation pages.
        </p>
        <p>
          The data of all mappings can be retrieved trough this API call:{" "}
          <a rel="noreferrer" target="_blank" href={apiAllMapsURL}>
            {"{JSON↗}"}
          </a>
        </p>
      </div>
      <NCITmapsSelection />
    </Layout>
  )
}

const NCITmapsSelection = withUrlQuery(({ urlQuery, setUrlQuery }) => {
  const { options: allOntologiesOptions } = useGetFilteredOptions({
    filters: prefixes,
    filterPrecision: filterPrecision
  })

  const [firstSelection, setFirstSelection] = useState(urlQuery.firstSelection)
  const handleFirstSelectionChange = (firstSelection) => {
    setUrlQuery({
      ...(firstSelection ? { firstSelection } : null)
    })
    setSecondSelection(null)
    setFirstSelection(firstSelection)
  }
  useEffect(() => {
    setFirstSelection(urlQuery.firstSelection)
  }, [urlQuery.firstSelection])

  const [secondSelection, setSecondSelection] = useState(
    urlQuery.secondSelection
  )
  const handleSecondSelectionChange = (secondSelection) => {
    setUrlQuery({
      ...(urlQuery.firstSelection
        ? { firstSelection: urlQuery.firstSelection }
        : null),
      ...(secondSelection ? { secondSelection } : null)
    })
    setSecondSelection(secondSelection)
  }
  useEffect(() => {
    setSecondSelection(urlQuery.secondSelection)
  }, [urlQuery.secondSelection])

  // compute second selection options
  const {
    isLoading: secondSelectionLoading,
    error: secondSelectionError,
    options: secondSelectionOptions
  } = useGetFilteredOptions({
    filters: firstSelection,
    filterResult: firstSelection
  })

  // compute result
  const selections = [firstSelection, secondSelection].filter((s) => !!s)
  let filters
  if (selections.length === 0) {
    filters = selections
  } else {
    filters = selections.join(",")
    filters = filters + "," + prefixes
  }
  const {
    data: resultsData,
    isLoading: resultsLoading,
    error: resultsError
  } = useOntologymaps({ filters })

  return (
    <div className="content">
      <h5>
        Code Selection
        <Infodot infoText={"Select or type (prefixed) NCIT or ICD-O code"} />
      </h5>
      <div className="mb-6">
        <CustomSelect
          className="mb-5"
          options={allOntologiesOptions}
          value={
            allOntologiesOptions.find((o) => o.value === firstSelection) ?? null
          }
          onChange={(option) => handleFirstSelectionChange(option?.value)}
          isClearable
          placeholder="First: Type & select NCIT or ICD-O code"
        />
        {firstSelection && (
          <Loader
            isLoading={secondSelectionLoading}
            hasError={secondSelectionError}
          >
            {secondSelectionOptions &&
            resultsData?.response.results[0].termGroups?.length > 1 ? (
              <CustomSelect
                className="mb-6"
                options={secondSelectionOptions}
                value={
                  secondSelectionOptions.find(
                    (o) => o.value === secondSelection
                  ) ?? null
                }
                onChange={(option) =>
                  handleSecondSelectionChange(option?.value)
                }
                isClearable
                placeholder="Optional: Limit with second selection"
              />
            ) : (
              <div> </div>
            )}
            <Loader isLoading={resultsLoading} hasError={resultsError}>
              {resultsData?.response.results[0].termGroups?.length > 0 ? (
                <CodeGroups
                  codeGroups={resultsData?.response.results[0].termGroups}
                  ontomapsUrl={ontologymapsPrefUrl({
                    filters,
                    filterPrecision
                  })}
                />
              ) : (
                <div className="notification">No groups found.</div>
              )}
            </Loader>
          </Loader>
        )}
      </div>
    </div>
  )
})
