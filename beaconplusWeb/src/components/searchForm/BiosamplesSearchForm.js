import {
  checkIntegerRange,
  makeFilters,
  useFiltersByType,
  validateBeaconQuery
} from "../../hooks/api"
import React, { useMemo, useState } from "react" //useEffect, 
import { useForm } from "react-hook-form"
import {
  CytoBandsUtility,
  GeneSpansUtility,
  useFormUtilities
} from "./BiosamplesFormUtilities"
import PropTypes from "prop-types"
import { merge, transform } from "lodash"
import SelectField from "../formShared/SelectField"
import InputField from "../formShared/InputField"
import {MarkdownParser} from "../MarkdownParser"
import useDeepCompareEffect from "use-deep-compare-effect"
import { withUrlQuery } from "../../hooks/url-query"
import { GeoCitySelector } from "./GeoCitySelector"
import ChromosomePreview from "./ChromosomePreview"
import { FaCogs } from "react-icons/fa"
import cn from "classnames"

export const BiosamplesSearchForm = withUrlQuery(
  ({ urlQuery, setUrlQuery, ...props }) => (
    <BeaconSearchForm {...props} urlQuery={urlQuery} setUrlQuery={setUrlQuery} />
  )
)
export default BiosamplesSearchForm

BiosamplesSearchForm.propTypes = {
  isQuerying: PropTypes.bool.isRequired,
  setSearchQuery: PropTypes.func.isRequired,
  beaconQueryTypes: PropTypes.object.isRequired,
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

function useIsFilterlogicWarningVisible(watch) {
  const filterLogic = watch("filterLogic")
  const bioontology = watch("bioontology")
  const referenceid = watch("referenceid")
  const clinicalClasses = watch("clinicalClasses")
  const cohorts = watch("cohorts")
  const allTermsFilters = watch("allTermsFilters")
  const sex = watch("sex")
  const materialtype = watch("materialtype")
  const ageAtDiagnosis = watch("ageAtDiagnosis")
  const followupTime = watch("followupTime")
  const followupState = watch("followupState")
  const freeFilters = watch("freeFilters")
  const filters = makeFilters({
    allTermsFilters,
    bioontology,
    referenceid,
    clinicalClasses,
    cohorts,
    sex,
    materialtype,
    ageAtDiagnosis,
    followupTime,
    followupState,
    freeFilters
  })
  return filterLogic === "AND" && filters.length > 1
}

export function BeaconSearchForm({
    isQuerying,
    setSearchQuery,
    beaconQueryTypes,
    requestTypeExamples,
    parametersConfig,
    urlQuery,
    setUrlQuery
  }) {
  // const autoExecuteSearch = urlQuery.executeSearch === "true"

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
    setValue,
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

  const {
    cytoBandPanelOpen,
    onCytoBandClick,
    onCytoBandCloseClick,
    geneSpansPanelOpen,
    onGeneSpansClick,
    onGeneSpansCloseClick
  } = useFormUtilities()

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

  const isFilterlogicWarningVisible = useIsFilterlogicWarningVisible(watch)
  const geoCity = watch("geoCity")
  const showGeoDistance = !parameters.geoCity.isHidden && geoCity != null

  return (
    <>
      <div>
        <QuerytypesTabs
          onQuerytypeClicked={handleQuerytypeClicked(
            reset,
            setExample,
            setUrlQuery
          )}
          beaconQueryTypes={beaconQueryTypes}
        />
        <form onSubmit={handleSubmit(onSubmit)}>
          {errors?.global?.message && (
            <div className="notification is-warning">
              {errors.global.message}
            </div>
          )}
          <SelectField {...parameters.assemblyId} {...selectProps} />
          {!parameters.datasetIds.isHidden && (
            <SelectField
              {...parameters.datasetIds} {...selectProps}
            />
          )}
          <div className="columns my-0">
            <InputField
              className={cn(
                !parameters.geneId.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.geneId} {...fieldProps}
            />
            <InputField
              className={cn(
                !parameters.genomicAlleleShortForm.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.genomicAlleleShortForm} {...fieldProps}
            />
            <InputField
              className={cn(
                !parameters.aminoacidChange.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.aminoacidChange} {...fieldProps}
            />
          </div>
          <div className="columns my-0">
            <SelectField
              className={cn(
                !parameters.analysisOperation.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.analysisOperation}
              {...selectProps}
            />
            <SelectField
              className={cn(
                !parameters.variantType.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.variantType}
              {...selectProps}
            />
          </div>
          <div className="columns my-0">
            <SelectField
              className={cn(
                !parameters.referenceName.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.referenceName}
              {...selectProps}
            />
            <InputField
              className={cn(
                !parameters.start.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.start}
              rules={{
                validate: checkIntegerRange
              }}
            />
            <InputField
              className={cn(!parameters.end.isHidden && "column", "py-0 mb-3")}
              {...fieldProps}
              {...parameters.end}
              rules={{
                validate: checkIntegerRange
              }}
            />
          </div>
          <div className="columns my-0">
            <SelectField
              className={cn(
                !parameters.mateName.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.mateName}
              {...selectProps}
            />
            <InputField
              className={cn(
                !parameters.mateStart.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.mateStart}
              rules={{
                validate: checkIntegerRange
              }}
            />
            <InputField
              className={cn(!parameters.mateEnd.isHidden && "column", "py-0 mb-3")}
              {...fieldProps}
              {...parameters.mateEnd}
              rules={{
                validate: checkIntegerRange
              }}
            />
          </div>
          <div className="columns my-0">
            <InputField
              className={cn(
                !parameters.variantMinLength.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.variantMinLength}
              rules={{
                validate: checkIntegerRange
              }}
            />
            <InputField
              className={cn(
                !parameters.variantMaxLength.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.variantMaxLength}
              rules={{
                validate: checkIntegerRange
              }}
            />
            <InputField
              className={cn(
                !parameters.referenceBases.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.referenceBases}
            />
            <InputField
              className={cn(
                !parameters.alternateBases.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.alternateBases}
            />
          </div>
          <InputField {...parameters.cytoBands} {...fieldProps} />
          <InputField {...parameters.variantQueryDigests} {...fieldProps} />
          <div className="columns my-0">
            <SelectField
              className={cn(
                !parameters.referenceid.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.referenceid}
              {...selectProps}
              isLoading={isRefSubsetsDataLoading}
            />
            <InputField
              className={cn(
                !parameters.cohorts.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.cohorts}
            />
          </div>
          <div className="columns my-0">
            <SelectField
              className={cn(
                !parameters.bioontology.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.bioontology}
              {...selectProps}
              isLoading={isBioSubsetsDataLoading}
            />
            <SelectField
              className={cn(
                !parameters.clinicalClasses.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.clinicalClasses}
              {...selectProps}
              isLoading={isClinicalDataLoading}
            />
          </div>
          <div className="columns my-0">
            <SelectField
              className={cn(
                !parameters.sex.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.sex}
              {...selectProps}
            />
            <InputField
              className={cn(
                !parameters.ageAtDiagnosis.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.ageAtDiagnosis}
            />
            <SelectField
              className={cn(
                !parameters.materialtype.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.materialtype}
              {...selectProps}
            />
          </div>

          <div className="columns my-0">
            <InputField
              className={cn(
                !parameters.followupTime.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.followupTime}
            />
            <SelectField
              className={cn(
                !parameters.followupState.isHidden && "column",
                "py-0 mb-3"
              )}
              {...parameters.followupState}
              {...selectProps}
            />
          </div>

          <div className="columns my-0">
            <SelectField
              className="column py-0 mb-3"
              {...parameters.allTermsFilters}
              {...selectProps}
              isLoading={isAllSubsetsDataLoading}
            />
            <SelectField
              className="column py-0 mb-3"
              {...parameters.filterLogic}
              {...selectProps}
              label={
                <span>
                  <span>{parameters.filterLogic.label}</span>
                  <FilterLogicWarning isVisible={isFilterlogicWarningVisible} />
                </span>
              }
            />
            <SelectField
              className="column py-0 mb-3"
              {...parameters.includeDescendantTerms}
              {...selectProps}
              label={
                <span>
                  <span>{parameters.includeDescendantTerms.label}</span>
                </span>
              }
            />
          </div>
          <InputField {...parameters.freeFilters} {...fieldProps} />
          <InputField {...parameters.accessid} {...fieldProps} />
          {!parameters.geoCity.isHidden && (
            <div className="columns my-0">
              <GeoCitySelector
                className={cn("column", "py-0 mb-3")}
                {...parameters.geoCity}
                {...selectProps}
              />
              <div
                className={cn("column", "py-0 mb-3", {
                  "is-invisible": !showGeoDistance,
                  "animate__fadeIn animate__animated": showGeoDistance
                })}
              >
                <InputField {...parameters.geodistanceKm} {...fieldProps} />
              </div>
            </div>
          )}
          <div className="columns my-0">
            <InputField
              className={cn(
                !parameters.limit.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.limit}
              rules={{
                validate: checkIntegerRange
              }}
            />
            <InputField
              className={cn(
                !parameters.skip.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.skip}
              rules={{
                validate: checkIntegerRange
              }}
            />
            <InputField
              className={cn(
                !parameters.includeResultsetResponses.isHidden && "column",
                "py-0 mb-3"
              )}
              {...fieldProps}
              {...parameters.includeResultsetResponses}
            />
          </div>
          <ChromosomePreview watch={watch} />
          <div className="field mt-5">
            <div className="control">
              <button
                type="submit"
                className={cn("button", "is-primary is-fullwidth", {
                  "is-loading": isQuerying
                })}
              >
                Query Database
              </button>
            </div>
          </div>
        </form>
      </div>
      <div style={{ "padding-top": "20px" }}>
        {geneSpansPanelOpen && (
          <GeneSpansUtility
            onClose={onGeneSpansCloseClick}
            setFormValue={setValue}
          />
        )}
        {cytoBandPanelOpen && (
          <CytoBandsUtility
            onClose={onCytoBandCloseClick}
            setFormValue={setValue}
          />
        )}
        <div className="buttons">
          <FormUtilitiesButtons
            onCytoBandClick={onCytoBandClick}
            cytoBandPanelOpen={cytoBandPanelOpen}
            onGeneSpansClick={onGeneSpansClick}
            geneSpansPanelOpen={geneSpansPanelOpen}
          />

        </div>
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
        {example?.description && (
          <ExampleDescription description={example.description} />   
        )}
      </div>
      {example?.img && (
          <div>
            <img src={example.img}/>
          </div>
      )}
    </>
  )
}

function QuerytypesTabs({ beaconQueryTypes, onQuerytypeClicked }) {
  // console.log(beaconQueryTypes)
  const startType = beaconQueryTypes[0]
  const [selectedTab, setSelectedTab] = useState(startType)
  // onQuerytypeClicked(selectedTab)
  return (
    <div className="tabs is-boxed">
      <ul>
        {Object.entries(beaconQueryTypes || []).map(([id, value]) => (
          <li
            className={cn({
              "is-active": selectedTab.label === value.label
            })}
            key={id}
            onClick={() => {onQuerytypeClicked(value), setSelectedTab(value)}}
          >
            <a>{value.label}</a>
          </li>
        ))}
      </ul>
    </div>
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
      <div className="columns">
        <div className="column is-one-fifth label">
          Query Examples
        </div>
        <div className="column">
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
      </div>
    </div>
  )
}

function FormUtilitiesButtons({
  onGeneSpansClick,
  geneSpansPanelOpen,
  onCytoBandClick,
  cytoBandPanelOpen
}) {
  return (
    <div className="column is-full" style={{ padding: "0px" }}>
      <div className="columns">
        <div className="column is-one-fifth label">
          Form Utilities
        </div>
        <div className="column is-full">
          <button
            className={cn("button is-warning", [geneSpansPanelOpen && "is-link"])}
            onClick={onGeneSpansClick}
          >
            <span className="icon">
              <FaCogs />
            </span>
            <span>Gene Spans</span>
          </button>
          <button
            className={cn("button is-warning", [cytoBandPanelOpen && "is-link"])}
            onClick={onCytoBandClick}
          >
            <span className="icon">
              <FaCogs />
            </span>
            <span>Cytoband(s)</span>
          </button>
        </div>
      </div>
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
    variantType,
    referenceName,
    mateName,
    referenceBases,
    alternateBases,
    start,
    end,
    mateStart,
    mateEnd,
    cytoBands,
    variantQueryDigests,
    geneId,
    aminoacidChange,
    genomicAlleleShortForm,
    bioontology,
    clinicalClasses,
    referenceid,
    cohorts,
    ageAtDiagnosis,
    followupTime,
    followupState,
    freeFilters,
    allTermsFilters
  } = formValues

  const errors = []
  const setMissing = (name) =>
    errors.push([name, { type: "manual", message: "Parameter is missing" }])

  if (
      !referenceName && 
      !referenceBases && 
      !alternateBases && 
      !start &&
      !end &&
      !variantQueryDigests &&
      !cytoBands &&
      !variantType &&
      !geneId &&
      !aminoacidChange &&
      !genomicAlleleShortForm &&
      !bioontology &&
      !referenceid &&
      !ageAtDiagnosis && 
      !followupTime && 
      !followupState && 
      !allTermsFilters &&
      !freeFilters &&
      !clinicalClasses &&
      !cohorts
  ) {
    !referenceName && setMissing("referenceName")
    !referenceBases && setMissing("referenceBases")
    !alternateBases && setMissing("alternateBases")
    !start && setMissing("start")
    !end && setMissing("end")
    !mateName && setMissing("mateName")
    !mateStart && setMissing("mateStart")
    !mateEnd && setMissing("mateEnd")
    !cytoBands && setMissing("cytoBands")
    !variantQueryDigests && setMissing("variantQueryDigests")
    !variantType && setMissing("variantType")
    !geneId && setMissing("geneId")
    !bioontology && setMissing("bioontology")
    !clinicalClasses && setMissing("clinicalClasses")
    !referenceid && setMissing("referenceid")
    !ageAtDiagnosis && setMissing("ageAtDiagnosis")
    !followupTime && setMissing("followupTime")
    !followupState && setMissing("followupState")
    !freeFilters && setMissing("freeFilters")
    !allTermsFilters && setMissing("allTermsFilters")
    !cohorts && setMissing("allTermsFilters")
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

const handleExampleClicked = (reset, setExample, setUrlQuery) => (example) => {
  setUrlQuery({}, { replace: true })
  setExample(example)
}

const handleQuerytypeClicked = (reset, setExample, setUrlQuery) => (example) => {
  setUrlQuery({}, { replace: true })
  setExample(example)
}

// Maps FilteringTerms hook to apiReply usable by DataFetchSelect
function useFilteringTerms(watchForm, ct) {
  const datasetIds = watchForm("datasetIds")
  return useFiltersByType({
    datasetIds,
    collationTypes: ct
  })
}

function FilterLogicWarning({ isVisible }) {
  return (
    <span
      className={cn(
        "has-background-warning has-text-weight-normal ml-2 px-1",
        "is-inline-flex animate__animated animate__headShake",
        { "is-hidden": !isVisible }
      )}
    >
      Multiple terms - use OR ?
    </span>
  )
}
