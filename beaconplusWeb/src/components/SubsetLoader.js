import {
  basePath,
  useServiceItemDelivery,
  sampleSearchPageFiltersLink,
  NoResultsHelp
} from "../hooks/api"
import { Loader } from "./Loader"
import { SubsetHistogram } from "./SVGloaders"
// import { ShowJSON } from "./RawData"
import { ExternalLink, InternalLink } from "./helpersShared/linkHelpers"

const service = "collations"

export function SubsetLoader({ id, datasetIds }) {
  const { data, error, isLoading } = useServiceItemDelivery(
    id,
    service,
    datasetIds
  )
  return (
    <Loader isLoading={isLoading} hasError={error} background>
      {data && (
        <SubsetResponse response={data} id={id} datasetIds={datasetIds} />
      )}
    </Loader>
  )
}

function SubsetResponse({ response, datasetIds }) {
  if (!response.response.results[0]) {
    return NoResultsHelp("subsetdetails")
  }
  return <Subset subset={response.response.results[0]} datasetIds={datasetIds} />
}

function Subset({ subset, datasetIds }) {
  
  const filters = subset.id
  const sampleFilterScope = "allTermsFilters"
      
  return (
<section className="content">
  <h2>
    {subset.label} ({subset.id})
  </h2>

  {subset.type && (
    <>
      <h5>Subset Type</h5>
      <ul>
        <li>
          {subset.type}{" "}
          <ExternalLink
            href={subset.reference}
            label={subset.id}
          />
        </li>
      </ul>
    </>
  )}

  <h5>Sample Counts</h5>
  <ul>
    <li>{subset.count} samples</li>
    <li>{subset.codeMatches} direct <i>{subset.id}</i> code  matches</li>
    {subset.cnvAnalyses && (
      <li>{subset.cnvAnalyses} CNV analyses</li>
    )}
    {subset.frequencymapCnvAnalyses && (
      <li>
        {subset.frequencymapCnvAnalyses} {" CNV analyses used in frequency calculations"}
      </li>
    )}
  </ul>
  <h5>CNV Histogram</h5>
  <div className="mb-3">
    <SubsetHistogram
      id={subset.id}
      datasetIds={datasetIds}
      loaderProps={{background: true, colored: true}}
    />
  </div>

  <h5>
    <InternalLink
      href={`${basePath}services/intervalFrequencies/${subset.id}/?output=pgxfreq`}
      label="Download CNV frequencies"
    />
  </h5>
  <p>
    Download CNV frequency data for genomic 1Mb bins.
  </p>

  <h5>
    <InternalLink
      href={ sampleSearchPageFiltersLink({datasetIds, sampleFilterScope, filters}) }
      label={`Search for ${subset.id} Samples`}
      rel="noreferrer"
      target="_blank"
    />
  </h5>
  <p>
    Select samples through the search form, e.g. by querying for specific
    genomic variants or phenotypes.
  </p> 

  {/*<ShowJSON data={subset} />*/}
  
</section>
  )
}
