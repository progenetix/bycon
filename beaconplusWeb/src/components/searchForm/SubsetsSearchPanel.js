import React, { useState } from "react"
import { useSubsetsQuery } from "../../hooks/api"
import Panel from "../Panel"
import { SubsetsSearchForm } from "./SubsetsSearchForm"
import { SubsetsResults } from "../searchResults/SubsetsResults"
import PropTypes from "prop-types"
// import cn from "classnames"

SubsetsSearchPanel.propTypes = {
  parametersConfig: PropTypes.object.isRequired,
  beaconQueryTypes: PropTypes.object.isRequired,
  requestTypeExamples: PropTypes.object.isRequired,
  collapsed: false
}

export default function SubsetsSearchPanel({
  parametersConfig,
  beaconQueryTypes,
  requestTypeExamples,
  collapsed
}) {
  
  const [query, setQuery] = useState(null) // actual valid query
  const [searchCollapsed, setSearchCollapsed] = useState(collapsed)

  const {
    // data: queryResponse,
    // error: queryError,
    mutate: mutateQuery,
    isLoading: isQueryLoading
  } = useSubsetsQuery(query)

  // console.log(useSubsetsQuery(query))

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
              <div className="column">Select Summary Histograms</div>
            }
            </div>
        }
      >
        <SubsetsSearchForm
          parametersConfig={parametersConfig}
          beaconQueryTypes={beaconQueryTypes}
          requestTypeExamples={requestTypeExamples}
          isQuerying={isLoading}
          setSearchQuery={onValidFormQuery}
        />
      </Panel>
      {query && (
        <SubsetsResults
          query={query}
        />
      )}
    </>
  )
}
