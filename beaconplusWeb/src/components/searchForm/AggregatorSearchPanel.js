import React, { useState } from "react"
import { useAggregatorQuery } from "../../hooks/api"
import Panel from "../Panel"
// import { FaSlidersH } from "react-icons/fa"
import { BiosamplesSearchForm } from "./BiosamplesSearchForm"
import { AggregatorResults } from "../searchResults/AggregatorResults"
import PropTypes from "prop-types"
// import cn from "classnames"

AggregatorSearchPanel.propTypes = {
  requestTypeConfig: PropTypes.object.isRequired,
  parametersConfig: PropTypes.object.isRequired,
  collapsed: false
}

export default function AggregatorSearchPanel({
  parametersConfig,
  requestTypeConfig,
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
  } = useAggregatorQuery(query)

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

  // button className="button ml-3"
  //    className="icon has-text-info"

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
              <div className="column">Search Variants</div>
            }
            </div>
        }
      >
        <BiosamplesSearchForm
          requestTypeConfig={requestTypeConfig}
          requestTypeExamples={requestTypeExamples}
          parametersConfig={parametersConfig}
          isQuerying={isLoading}
          setSearchQuery={onValidFormQuery}
        />
      </Panel>
      {query && (
        <AggregatorResults
          isLoading={isLoading}
          response={queryResponse}
          error={queryError}
          query={query}
        />
      )}
    </>
  )
}
