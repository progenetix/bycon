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
const prefixes = "UBERON,pgx:icdot"
const apiAllMapsURL = `${ontologymapsBaseUrl}filters=${prefixes}`

export default function UBERONmapsPage() {
  return (
    <Layout title="Ontologymaps" headline="Services: Ontologymaps (UBERON)">
      <div className="content">
        <img
          src="/img/uberon-logo-120x120.png"
          className="Layout__img__topright Layout__img__width-40"
        />
        <p>
          The <strong>ontologymaps</strong> service provides equivalency mapping
          between ICD-O and other classification systems, notably NCIt and
          UBERON. It makes use of the sample-level mappings developed for the
          individual samples in the Progenetix collection.
        </p>
        <h4>UBERON and ICD-O 3</h4>
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
      <UBERONmapsSelection
        prefixes={prefixes}
        filterPrecision={filterPrecision}
      />
    </Layout>
  )
}

const UBERONmapsSelection = withUrlQuery(({ urlQuery, setUrlQuery }) => {
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
        <Infodot infoText={"Select or type (prefixed) UBERON or ICD-O code"} />
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
          placeholder="Type & select UBERON or ICD-O Topography code"
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
              <div></div>
            )}
            <Loader isLoading={resultsLoading} hasError={resultsError}>
              {resultsData?.response.results[0].termGroups?.length > 0 ? (
                <CodeGroups
                  prefixes={prefixes}
                  codeGroups={resultsData?.response.results[0].termGroups}
                  ontomapsUrl={ontologymapsPrefUrl({ prefixes, filters })}
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
