import React, { useState } from "react"
import { useBeaconQuery } from "../../hooks/api"
import Panel from "../Panel"
import { BiosamplesSearchForm } from "./BiosamplesSearchForm"
import { BiosamplesResults } from "../searchResults/BiosamplesResults"
import PropTypes from "prop-types"
// import cn from "classnames"

BiosamplesSearchPanel.propTypes = {
  parametersConfig: PropTypes.object.isRequired,
  beaconQueryTypes: PropTypes.object.isRequired,
  requestTypeExamples: PropTypes.object.isRequired,
  collapsed: false
}

export default function BiosamplesSearchPanel({
  parametersConfig,
  beaconQueryTypes,
  requestTypeExamples,
  collapsed
}) {
  const [query, setQuery] = useState(null) // actual valid query
  const [searchCollapsed, setSearchCollapsed] = useState(collapsed)

  const {
    data: queryResponse,
    error: queryError,
    mutate: mutateQuery,
    isLoading: isQueryLoading
  } = useBeaconQuery(query)

  const clearQuery = () => {
    setQuery(null)
    mutateQuery(null)
  }
  const isLoading = isQueryLoading && !!query
  const onValidFormQuery = (formValues) => {
    setSearchCollapsed(true)
    clearQuery()
    setQuery(formValues)
  }

  return  (
    <>
      <Panel
        isOpened={!searchCollapsed}
        heading={
            <div className="columns">
              {(searchCollapsed && (
                <div className="column">
                  <button
                    className="button is-info mb-5"
                    onClick={() => {
                      clearQuery()
                      setSearchCollapsed(false)
                    }}
                  >
                    Edit Query
                  </button>
                </div>
              ))
               ||
              <div className="column">Search Samples</div>
            }
            </div>
        }
      >
        <BiosamplesSearchForm
          parametersConfig={parametersConfig}
          beaconQueryTypes={beaconQueryTypes}
          requestTypeExamples={requestTypeExamples}
          isQuerying={isLoading}
          setSearchQuery={onValidFormQuery}
        />
      </Panel>
      {query && (
        <BiosamplesResults
          isLoading={isLoading}
          response={queryResponse}
          error={queryError}
          query={query}
        />
      )}
    </>
  )
}
