import swr from "swr"
import defaultFetcher, { svgFetcher } from "./fetcher"
import { keyBy } from "lodash"
import SiteConfig from "../site-specific/config.js"

// eslint-disable-next-line no-undef
export const basePath = process.env.NEXT_PUBLIC_API_PATH
export const useProxy = process.env.NEXT_PUBLIC_USE_PROXY === "true"

export function useExtendedSWR(url, fetcher = defaultFetcher) {
  const { data, error, ...other } = swr(url, fetcher)
  return { data, error, ...other, isLoading: !data && !error }
}

// export const MAX_HISTO_SAMPLES = 1000
export const THISSITE = process.env.NEXT_PUBLIC_SITE_URL
export const THISYEAR = new Date().getFullYear()
export const BIOKEYS = ["icdoMorphology", "icdoTopography", "histologicalDiagnosis"]
export const DATASETDEFAULT = SiteConfig.default_dataset_id

export function useProgenetixApi(...args) {
  const { data, error, ...other } = useExtendedSWR(...args)
  if (data) {
    const errorMessage = findErrorMessage(data)
    // Compatible with the simple responses.
    return { ...other, data, error: errorMessage ?? error }
  }
  // Connection error or http error code
  else if (error) {
    const errorMessage = error.info
      ? findErrorMessage(error.info)
      : error.message
    return { ...other, error: errorMessage }
  } else {
    return { ...other }
  }
}

// Return an error message contained in the payload.
function findErrorMessage(data) {
  return (
    data.error?.errorMessage ||
    (data.errors ? errorsToMessage(data.errors) : null) ||
    null
  )
}

function errorsToMessage(errors) {
  return errors.join(", ")
}

export async function tryFetch(url, fallBack = "N/A") {
  console.info(`Fetching data from ${url}.`)
  try {
    const response = await fetch(url)
    return response.json()
  } catch (e) {
    console.error(`Count not fetch ${url}`)
    if (fallBack) {
      console.info(`Using ${JSON.stringify(fallBack)} as fallBack`)
      return fallBack
    } else {
      throw e
    }
  }
}
/**
 * When param is null no query will be triggered.
 */

export function urlRetrieveIds(urlQuery) {
  var { id, datasetIds } = urlQuery
  if (!datasetIds) {
    datasetIds = DATASETDEFAULT
  }
  return { id, datasetIds }
}


// This Beacon query only retrieves the counts & handovers using a custom `includeHandovers=true`
// parameter, to avoid "double-loading" of the results.
export function useBeaconQuery(queryData) {
  return useProgenetixApi(
    queryData
      ? `${basePath}beacon/biosamples/?includeHandovers=true&requestedGranularity=aggregated&${buildQueryParameters(queryData)}`
      : null
  )
}

export function useSubsetsQuery(queryData) {
  return useProgenetixApi(
    queryData
      ? `${basePath}services/collationplots/?${buildFilterParameters(queryData)}`
      : null
  )
}

export function useAggregatorQuery(queryData) {
  return useProgenetixApi(
    queryData
      ? `${basePath}services/aggregator/?requestedGranularity=boolean&${buildQueryParameters(queryData)}`
      : null
  )
}

export function validateBeaconQuery(queryData) {
  try {
    buildQueryParameters(queryData)
    return null
  } catch (e) {
    return e
  }
}

export function mkGeoParams(geoCity, geodistanceKm) {
  if (!geoCity) return null
  const coordinates = geoCity.data.geoLocation.geometry.coordinates ?? []
  const [geoLongitude, geoLatitude] = coordinates
  const geoDistance = geodistanceKm ? geodistanceKm * 1000 : 100 * 1000
  return { geoLongitude, geoLatitude, geoDistance }
}

export function makePlotGeneSymbols({
  plotGeneSymbols
}) {
  var geneSymbols = []
  if (plotGeneSymbols) {
    for (let i = 0; i < plotGeneSymbols.length; i++) {
      geneSymbols.push(plotGeneSymbols[i].value)
    }
  }
  return geneSymbols
}

export function makeFilters({
  allTermsFilters,
  clinicalClasses,
  bioontology,
  referenceid,
  analysisOperation,
  cohorts,
  sex,
  materialtype,
  ageAtDiagnosis,
  followupTime,
  followupState,
  freeFilters
}) {
  return [
    ...(allTermsFilters ?? []),
    ...(bioontology ?? []),
    ...(clinicalClasses ?? []),
    ...(referenceid ?? []),
    ...(cohorts ? [cohorts] : []),
    ...(analysisOperation ? [analysisOperation] : []),
    ...(materialtype ? [materialtype] : []),
    ...(sex ? [sex] : []),
    ...(ageAtDiagnosis ? ["ageAtDiagnosis:"+ageAtDiagnosis] : []),
    ...(followupTime ? ["followupTime:"+followupTime] : []),
    ...(followupState ? [followupState] : []),
    ...(freeFilters ? freeFilters.split(",") : [])
  ]
}

export function buildFilterParameters(queryData) {
  const {
    bioontology,
    referenceid,
    cohorts,
    analysisOperation,
    sex,
    materialtype,
    allTermsFilters,
    clinicalClasses,
    ageAtDiagnosis,
    followupTime,
    followupState,
    freeFilters
  } = queryData

  const filters = makeFilters({
    allTermsFilters,
    clinicalClasses,
    bioontology,
    referenceid,
    cohorts,
    analysisOperation,
    sex,
    materialtype,
    ageAtDiagnosis,
    followupTime,
    followupState,
    freeFilters
  })
  return new URLSearchParams(
    flattenParams([
      ["filters", filters]
    ]).filter(([, v]) => !!v)
  ).toString()
}

export function buildQueryParameters(queryData) {
  const {
    start,
    end,
    bioontology,
    referenceid,
    cohorts,
    analysisOperation,
    sex,
    materialtype,
    allTermsFilters,
    ageAtDiagnosis,
    followupTime,
    followupState,
    freeFilters,
    clinicalClasses,
    geoCity,
    geodistanceKm,
    ...otherParams
  } = queryData
  // positions from the form have to be -1 adjusted (only first value if interval)

  const starts = []
  if (start) {
    const match = INTEGER_RANGE_REGEX.exec(start)
    if (!match) throw new Error("incorrect start range")
    const [, start0, start1] = match
    var s0 = start0 - 1
    s0 = s0.toString()
    starts.push(s0)
    start1 && starts.push(start1)
  }
  const ends = []
  if (end) {
    const match = INTEGER_RANGE_REGEX.exec(end)
    if (!match) throw new Error("incorrect end range")
    const [, end0, end1] = match
    ends.push(end0)
    end1 && ends.push(end1)
  }
  const filters = makeFilters({
    allTermsFilters,
    clinicalClasses,
    bioontology,
    referenceid,
    cohorts,
    analysisOperation,
    sex,
    materialtype,
    ageAtDiagnosis,
    followupTime,
    followupState,
    freeFilters
  })
  const geoParams = mkGeoParams(geoCity, geodistanceKm) ?? {}
  return new URLSearchParams(
    flattenParams([
      ...Object.entries({ ...otherParams, ...geoParams }),
      ["start", starts],
      ["end", ends],
      ["filters", filters]
    ]).filter(([, v]) => !!v)
  ).toString()
}


export function useDataVisualization(queryData) {
  var q_path = "beacon/biosamples"
  if (queryData.fileId && queryData.fileId != "null") {
    q_path = "services/sampleplots"
  }
  return useProgenetixApi(
    queryData
      ? `${basePath}${q_path}/?${buildDataVisualizationParameters(
          queryData
        )}`
      : null
  )
}

export function getVisualizationLink(datasetIds, accessId, fileId, skip, limit, count) {
  return `/service-collection/dataVisualization?datasetIds=${datasetIds}&accessid=${accessId}&fileId=${fileId}&sampleCount=${count}&skip=${skip}&limit=${limit}`
}

export function buildDataVisualizationParameters(queryData) {
  return new URLSearchParams(
    flattenParams([...Object.entries(queryData)]).filter(([, v]) => !!v)
  ).toString()
}

export function publicationDataUrl(id) {
  return `${basePath}services/publications?filters=${id}`
}

export function usePublication(id) {
  return useProgenetixApi(publicationDataUrl(id))
}

export function usePublicationList({ geoCity, geodistanceKm }) {
  const qParams = new URLSearchParams({
    ...mkGeoParams(geoCity, geodistanceKm),
    filters: "pubmed,genomes:>0",
    method: "details"
  }).toString()
  const url = `${basePath}services/publications?${qParams}`
  return useProgenetixApi(url)
}

// ZHAW fetch

export function useLiteratureSearchResults(t1s,t2s)
{
  return useProgenetixApi(`${basePath}cgi-bin/literatureSearch/literatureSearch.py?func=search&mode=exact&t1s=${t1s.join(",")}&t2s=${t2s.join(",")}`);
}

export function useLiteratureCellLineMatches(cln)
{
  return useProgenetixApi(`${basePath}cgi-bin/literatureSearch/literatureSearch.py?func=relations&t1=${cln}`);
}

// \ ZHAW

export function usePublicationWithDataList({ geoCity, geodistanceKm }) {
  const qParams = new URLSearchParams({
    ...mkGeoParams(geoCity, geodistanceKm),
    filters: "pubmed,progenetix:>0",
    method: "details"
  }).toString()
  const url = `${basePath}services/publications?${qParams}`
  return useProgenetixApi(url)
}

// ,genomes:>0

export function useProgenetixRefPublicationList({ geoCity, geodistanceKm }) {
  const qParams = new URLSearchParams({
    ...mkGeoParams(geoCity, geodistanceKm),
    filters: "pubmed,pgxuse:yes",
    method: "details"
  }).toString()
  const url = `${basePath}services/publications?${qParams}`
  return useProgenetixApi(url)
}

export const ontologymapsBaseUrl = `${basePath}services/ontologymaps?`

export function ontologymapsUrl({ filters, filterPrecision }) {
  let params = new URLSearchParams({ filters: filters })
  if (filterPrecision) {
    params.append("filterPrecision", filterPrecision)
  }
  return `${ontologymapsBaseUrl}${params.toString()}`
}

export function ontologymapsPrefUrl({ prefixes, filters }) {
  return `${ontologymapsBaseUrl}filters=${prefixes},${filters}&filterPrecision=start`
}

export function useDataItemDelivery(id, entity, datasetIds) {
  return useProgenetixApi(getDataItemUrl(id, entity, datasetIds))
}

export function getDataItemUrl(id, entity, datasetIds) {
  return `${basePath}beacon/${entity}/${id}/?datasetIds=${datasetIds}`
}

export function useServiceItemDelivery(id, service, datasetIds) {
  return useProgenetixApi(getServiceItemUrl(id, service, datasetIds))
}

export function getServiceItemUrl(id, service, datasetIds) {
  return `${basePath}services/${service}?filters=${id}&datasetIds=${datasetIds}`
}

export function NoResultsHelp(entity) {
  return (
    <div className="notification is-size-5">
      This page will only show content if called with an existing {entity}{" "}
      &quot;id&quot; value.
    </div>
  )
}

export function useCytomapper(querytext) {
  const url =
    querytext &&
    querytext.length > 0 &&
    `${basePath}services/cytomapper/?cytoBands=${querytext}`
  return useProgenetixApi(url)
}

export function useSubsethistogram({
  datasetIds,
  id,
  fileId,
  plotType,
  plotRegionLabels,
  plotGeneSymbols,
  plotCytoregionLabels,
  size,
  plotChros,
  plotParsString
}) {
  const svgbaseurl = subsetHistoBaseLink(id, datasetIds)
  const params = []
  const plotParsVals = []
  fileId && params.push(["fileId", fileId])
  plotType && params.push(["plotType", plotType])
  size && plotParsVals.push("plot_width="+size)
  plotRegionLabels && plotParsVals.push("plot_region_labels="+plotRegionLabels.join(","))
  plotGeneSymbols && plotParsVals.push("plot_gene_symbols="+plotGeneSymbols.join(","))
  plotCytoregionLabels && plotParsVals.push("plot_cytoregion_labels="+plotCytoregionLabels.join(","))
  plotChros && plotParsVals.push("plot_chros="+plotChros.join(","))
  plotParsString && plotParsVals.push(plotParsString)
  plotParsVals.length > 0 && params.push(["plotPars", plotParsVals.join("::")])
  const searchQuery = new URLSearchParams(params).toString()
  return useExtendedSWR(size > 0 && `${svgbaseurl}&${searchQuery}`, svgFetcher)
}


export function useCollationsById({ datasetIds }) {
  if (! datasetIds) {
    datasetIds = DATASETDEFAULT
  }
  const { data, ...other } = useFiltersByType({
    collationTypes: "",
    datasetIds
  })

  if (data) {
    const mappedResults = keyBy(data.response.filteringTerms, "id")
    return {
      data: {
        ...data,
        results: mappedResults
      },
      ...other
    }
  }
  return { data, ...other }
}


export function useFiltersByType({ datasetIds, collationTypes }) {
  // TODO: construct URL w/o optional parameters if empty
  if (! datasetIds) {
    datasetIds = DATASETDEFAULT
  }
  const url = `${basePath}beacon/datasets/${datasetIds}/filtering_terms/?collationTypes=${collationTypes}`
  return useProgenetixApi(url)
}

// general site listings for collations etc. are bound to the default dataset
export function useFilterTreesByType({ datasetIds, collationTypes }) {
  if (! datasetIds) {
    datasetIds = DATASETDEFAULT
  }
  const url = `${basePath}beacon/datasets/${datasetIds}/filtering_terms?collationTypes=${collationTypes}&mode=termTree`
  return useProgenetixApi(url)
}

export function sampleSearchPageFiltersLink({
  datasetIds,
  sampleFilterScope,
  filters
}) {
  return `/search/?${sampleFilterScope}=${filters}&datasetIds=${datasetIds}`
}

export function subsetSearchPageFiltersLink({
  datasetIds,
  sampleFilterScope,
  filters
}) {
  return `/subsetsSearch/?${sampleFilterScope}=${filters}&datasetIds=${datasetIds}`
}

export function useGeoCity({ city }) {
  const url = city ?`${basePath}services/geolocations?city=${city}` : null
  return useProgenetixApi(url)
}

export function useGeneSymbol({ geneId }) {
  const url = geneId ? `${basePath}services/genespans/?geneId=${geneId}&filterPrecision=start&deliveryKeys=symbol,referenceName,chromosome,start,end` : null
  return useProgenetixApi(url)
}

export function subsetHistoBaseLink(id, datasetIds) {
  return `${basePath}services/collationplots/?datasetIds=${datasetIds}&filters=${id}`
}

// the targets are resolved by `bycon` (bycon/services/ids.py)
// TODO: make this a function here - UI links resolved in UI, API links in bycon
export function subsetIdLink(id) {
  return `${basePath}services/ids/${id}`
}

export function subsetPgxsegLink(id) {
  return `${basePath}services/intervalFrequencies/?&output=pgxseg&filters=${id}`
}

export async function uploadFile(formData) {
  // Default options are marked with *
  const response = await fetch(`${basePath}services/uploader/`, {
    method: "POST",
    headers: {},
    body: formData
  })
  return response.json()
}

// Transforms [[k1, v1], [k2, [v2, v3]]] into [[k1, v1], [k2, v2], [k3, v3]]
function flattenParams(paramArray) {
  return paramArray.flatMap(([key, value]) => {
    if (Array.isArray(value)) {
      return value.map((v) => [key, v])
    } else {
      return [[key, value]]
    }
  })
}

export const INTEGER_RANGE_REGEX = /^(\d+)(?:[-,;])?(\d+)?$/

export const checkIntegerRange = (value) => {
  if (!value) return
  const match = INTEGER_RANGE_REGEX.exec(value)
  if (!match) return "Input should be a range (ex: 1-5) or a single value"
  const [, range0Str, range1Str] = match
  const range0 = Number.parseInt(range0Str)
  const range1 = Number.parseInt(range1Str)
  if (range1 && range0 > range1)
    return "Incorrect range input, max should be greater than min"
}

export function replaceWithProxy(
  url,
  useProxyOpt = useProxy,
  basePathOpt = basePath
) {
  if (!url) return false
  if (!useProxyOpt) return url
  return url.toString().replace(new URL(url).origin + "/", basePathOpt)
}

