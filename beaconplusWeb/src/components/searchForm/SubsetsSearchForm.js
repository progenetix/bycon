import {
  // makeFilters,
  useFiltersByType,
  validateBeaconQuery
} from "../../hooks/api"
import React, { useMemo, useState } from "react" //useEffect, 
import { useForm } from "react-hook-form"
import PropTypes from "prop-types"
import {MarkdownParser} from "../MarkdownParser"
import { merge, transform } from "lodash"
import SelectField from "../formShared/SelectField"
import InputField from "../formShared/InputField"
import {GeneSymbolSelector} from "../formShared/GeneSymbolSelector"
import useDeepCompareEffect from "use-deep-compare-effect"
import { withUrlQuery } from "../../hooks/url-query"
import cn from "classnames"

export const SubsetsSearchForm = withUrlQuery(
  ({ urlQuery, setUrlQuery, ...props }) => (
    <SubsetSearchForm {...props} urlQuery={urlQuery} setUrlQuery={setUrlQuery} />
  )
)
export default SubsetsSearchForm

SubsetsSearchForm.propTypes = {
  isQuerying: PropTypes.bool.isRequired,
  setSearchQuery: PropTypes.func.isRequired,
  requestTypeExamples: PropTypes.object.isRequired,
  parametersConfig: PropTypes.object.isRequired
}

function urlQueryToFormParam(urlQuery, key, parametersConfig) {
  const isMulti = !!parametersConfig.parameters[key]?.isMulti ?? false
  const value = urlQuery[key]
  if (value == null) return value
  if (isMulti) {
    return value?.split(",").filter((v) => v?.trim().length ?? -1 > 0)
  } else return value
}

function SubsetSearchForm({
    isQuerying,
    setSearchQuery,
    requestTypeExamples,
    parametersConfig,
    urlQuery,
    setUrlQuery
  }) {

  const [example, setExample] = useState(null)
  let parameters = useMemo(
    () =>
      makeParameters(parametersConfig, example),
    [example, parametersConfig]
  )

  const initialValues = transform(parameters, (r, v, k) => {
    r[k] =
      urlQueryToFormParam(urlQuery, k, parametersConfig) ??
      v.defaultValue ??
      null
  })

  const {
    register,
    handleSubmit,
    errors,
    reset,
    setError,
    clearErrors,
    watch,
    control
  } = useForm({ defaultValues: initialValues })

  Object.keys(errors).length && console.info("Found errors in form", errors)

  // reset form when default values changes
  useDeepCompareEffect(() => reset(initialValues), [initialValues])
  
  // all subsets lookup ----------------------------------------------------- //
  var ct = ""
  const {
    data: allsubsetsResponse,
    isLoading: isAllSubsetsDataLoading 
  } = useFilteringTerms( watch, ct, "withpubmed" )
  const allsubsetsOptions = allsubsetsResponse?.response?.filteringTerms?.map((value) => ({
    value: value.id,
    label: `${value.id}: ${value.label} (${value.count})`
  }))
  parameters = merge({}, parameters, {
    allTermsFilters: { options: allsubsetsOptions }
  })

  // biosubsets lookup ------------------------------------------------------ //
  ct = "NCIT,icdom,icdot,UBERON"
  const {
    data: biosubsetsResponse,
    isLoading: isBioSubsetsDataLoading
  } = useFilteringTerms( watch, ct ) 
  const biosubsetsOptions = biosubsetsResponse?.response?.filteringTerms?.map((value) => ({
    value: value.id,
    label: `${value.id}: ${value.label} (${value.count})`
  }))
  parameters = merge({}, parameters, {
    bioontology: { options: biosubsetsOptions }
  })
  
  // referenceid lookup ----------------------------------------------------- //
  ct = "pubmed,GEOseries,AEseries,GEOplatform,cellosaurus"
  const {
    data: refsubsetsResponse,
    isLoading: isRefSubsetsDataLoading
  } = useFilteringTerms( watch, ct )
  const refsubsetsOptions = refsubsetsResponse?.response?.filteringTerms?.map((value) => ({
    value: value.id,
    label: `${value.id}: ${value.label} (${value.count})`
  }))   
  parameters = merge({}, parameters, {
    referenceid: { options: refsubsetsOptions }
  })
  
  // clinical lookup -------------------------------------------------------- //
  ct = "TNM,NCITgrade,NCITstage,EFOfus"
  const {
    data: clinicalResponse,
    isLoading: isClinicalDataLoading
  } = useFilteringTerms( watch, ct )
  const clinicalOptions = clinicalResponse?.response?.filteringTerms?.map((value) => ({
    value: value.id,
    label: `${value.id}: ${value.label} (${value.count})`
  }))
  parameters = merge({}, parameters, {
    clinicalClasses: { options: clinicalOptions }
  })

  // ======================================================================== //

  const onSubmit = onSubmitHandler({
    clearErrors,
    setError,
    setSearchQuery
  })

  // shortcuts
  const fieldProps = { errors, register }
  const selectProps = {
    ...fieldProps,
    control
  }

  // Note: Which of the fields is displayed is determined in 
  // config/subsetsSearchParametersMods.

  return (
    <>
      <article className="message is-info">
        <div className="message-body">
          <div className="content">{MarkdownParser(`On this page you can combine one or multiple disease or other
      codes from one or more datasets, to display their CNV profiles (regional CNV frequencies).
      These based on pre-computed CNV frequencies for the given code; for a combination of parameters
      please go to the [Search Page](/search/).`)}</div>
        </div>
      </article>
      <div>
       <form onSubmit={handleSubmit(onSubmit)}>
          {errors?.global?.message && (
            <div className="notification is-warning">
              {errors.global.message}
            </div>
          )}
          <SelectField
            {...parameters.datasetIds} {...selectProps}
          />               
          <SelectField
            className="column, py-0 mb-3"
            {...parameters.referenceid}
            {...selectProps}
            isLoading={isRefSubsetsDataLoading}
          />
          <SelectField
            {...parameters.bioontology}
            {...selectProps}
            isLoading={isBioSubsetsDataLoading}
          />
          <SelectField
            {...parameters.referenceid}
            {...selectProps}
            isLoading={isRefSubsetsDataLoading}
          />
          <SelectField
            {...parameters.clinicalClasses}
            {...selectProps}
            isLoading={isClinicalDataLoading}
          />
          <SelectField
            {...parameters.allTermsFilters}
            {...selectProps}
            isLoading={isAllSubsetsDataLoading}
          />
{/*          <GeneSymbolSelector
            {...parameters.plotGeneSymbols}
            {...selectProps}
          />
*/}       
          <SelectField
            {...parameters.plotType}
            {...selectProps}
          />
          <GeneSymbolSelector
            {...selectProps}
            name="plotGeneSymbols"
            label="Gene Symbol(s) for Labeling"
          />
          <InputField
            {...parameters.plotChros}
            {...fieldProps}
          />
          <InputField
            {...parameters.plotParsString}
            {...fieldProps}
          />
          <div className="field mt-5">
            <div className="control">
              <button
                type="submit"
                className={cn("button", "is-primary is-fullwidth", {
                  "is-loading": isQuerying
                })}
              >
                Retrieve CNV Profiles
              </button>
            </div>
          </div>
        </form>
      </div>
      <div style={{ "padding-top": "20px" }}>
        <div className="buttons">
          <ExamplesButtons
            onExampleClicked={handleExampleClicked(
              reset,
              setExample,
              setUrlQuery
            )}
            requestTypeExamples={requestTypeExamples}
          />
        </div>
        <ExampleDescription example={example} />   
      </div>  
      </>
  )
}

export function InfodotTab(short, full) {
  return (
    <span>
      <a alt={full}>{short}</a>
    </span>
  )
}

function ExamplesButtons({ requestTypeExamples, onExampleClicked }) {
  return (
    <div className="column is-full" style={{ padding: "0px" }}>
      {Object.entries(requestTypeExamples || []).map(([id, value]) => (
        <button
          key={id}
          className="button is-link is-outlined"
          onClick={() => onExampleClicked(value)}
        >
          {value.label}
        </button>
      ))}
    </div>
  )
}


function ExampleDescription({ example }) {
  return example?.description ? (
    <article className="message is-info">
      <div className="message-body">
        <div className="content">{MarkdownParser(example?.description)}</div>
      </div>
    </article>
  ) : null
}

function makeParameters(
  parametersConfig,
  example
) {
  // merge base parameters config and request config
  const mergedConfigs = merge(
    {}, // important to not mutate the object
    parametersConfig.parameters,
    example?.parameters ?? {}
  )
  // add name the list
  let parameters = transform(mergedConfigs, (r, v, k) => {
    r[k] = { name: k, ...v }
  })
  return parameters
}

function onSubmitHandler({ clearErrors, setError, setSearchQuery }) {
  return (values) => {
    clearErrors()
    // At this stage individual parameters are already validated.
    const errors = validateForm(values)
    if (errors.length > 0) {
      errors.forEach(([name, error]) => setError(name, error))
    } else {
      setSearchQuery(values)
    }
  }
}

function validateForm(formValues) {
  const {
    datasetIds,
    bioontology,
    clinicalClasses,
    referenceid,
    cohorts,
    freeFilters,
    allTermsFilters
  } = formValues

  const errors = []
  const setMissing = (name) =>
    errors.push([name, { type: "manual", message: "Parameter is missing" }])

  if (!bioontology && !referenceid && !allTermsFilters && !freeFilters && !clinicalClasses && !cohorts) {
    !bioontology && setMissing("bioontology")
    !clinicalClasses && setMissing("clinicalClasses")
    !referenceid && setMissing("referenceid")
    !freeFilters && setMissing("freeFilters")
    !allTermsFilters && setMissing("allTermsFilters")
    !cohorts && setMissing("allTermsFilters")
  }

  if (!datasetIds) {
    setMissing("datasetIds")
  }

  const queryError = validateBeaconQuery(formValues)
  if (queryError) {
    const error = {
      type: "manual",
      message: "Cannot build the database query."
    }
    errors.push(["global", error])
  }
  return errors
}

// Maps FilteringTerms hook to apiReply usable by DataFetchSelect
function useFilteringTerms(watchForm, ct) {
  const datasetIds = watchForm("datasetIds")
  return useFiltersByType({
    datasetIds,
    collationTypes: ct
  })
}

const handleExampleClicked = (reset, setExample, setUrlQuery) => (example) => {
  setUrlQuery({}, { replace: true })
  setExample(example)
  console.log("Example clicked", example)

}



