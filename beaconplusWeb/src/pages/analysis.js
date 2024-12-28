import {
  useDataItemDelivery,
  NoResultsHelp,
  urlRetrieveIds
} from "../hooks/api"
import { InternalLink } from "../components/helpersShared/linkHelpers"

import { Loader } from "../components/Loader"
import { withUrlQuery } from "../hooks/url-query"
import { Layout } from "../site-specific/Layout"

const itemColl = "analyses"
// const exampleId = "pgxcs-kftvlijb"

const AnalysisDetailsPage = withUrlQuery(({ urlQuery }) => {
  const { id, datasetIds, hasAllParams } = urlRetrieveIds(urlQuery)
  return (
    <Layout title="Analysis Details" headline="Analysis Details">
      {!hasAllParams ? (
        NoResultsHelp(itemColl)
      ) : (
        <AnalysisLoader csId={id} datasetIds={datasetIds} />
      )}
    </Layout>
  )
})

export default AnalysisDetailsPage

function AnalysisLoader({ csId, datasetIds }) {
  const { data, error, isLoading } = useDataItemDelivery(
    csId,
    itemColl,
    datasetIds
  )
  return (
    <Loader isLoading={isLoading} hasError={error} background>
      {data && (
        <AnalysisResponse response={data} csId={csId} datasetIds={datasetIds} />
      )}
    </Loader>
  )
}

function AnalysisResponse({ response, csId, datasetIds }) {
  if (!response.response.resultSets[0].results) {
    return NoResultsHelp(itemColl)
  }
  return <Analysis analysis={response.response.resultSets[0].results[0]} csId={csId} datasetIds={datasetIds} />
}

function Analysis({ analysis, csId, datasetIds }) {
  return (

<section className="content">
  <h3 className="mb-6">
    {csId}
  </h3>

  {analysis.description && (
    <>
      <h5>Description</h5>
      <p>{analysis.description}</p>
    </>
  )}

  {analysis.biosampleId && (
    <>
      <h5>Biosample</h5>
      <p>
        <InternalLink
          href={`/biosample?id=${analysis.biosampleId}&datasetIds=${datasetIds}`}
          label={analysis.biosampleId}
        />
      </p>
    </>
  )}

  <h5>Download</h5>
  <ul>
    <li>Analysis data as{" "}
      <InternalLink
        href={`/beacon/analyses/${csId}`}
        label="Beacon JSON"
      />
    </li>
    <li>Sample data as{" "}
      <InternalLink
        href={`/beacon/analyses/${csId}/biosamples`}
        label="Beacon biosample JSON"
      />
    </li>
    <li>Analysis variants as{" "}
      <InternalLink
        href={`/beacon/analyses/${csId}/genomicVariations`}
        label="Beacon JSON"
      />
    </li>
    <li>Analysis variants as{" "}
      <InternalLink
        href={`/services/pgxsegvariants?datasetIds=${datasetIds}&analysis_ids=${csId}`}
        label="Progenetix .pgxseg file"
      />
    </li>
    <li>Analysis variants as{" "}
      <InternalLink
        href={`/services/vcfvariants?datasetIds=${datasetIds}&analysis_ids=${csId}`}
        label="(experimental) VCF 4.4 file"
      />
    </li>
  </ul>

</section>)
  
}
