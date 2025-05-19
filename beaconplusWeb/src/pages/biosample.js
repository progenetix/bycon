import React, { useEffect, useState } from "react"
import {
  BIOKEYS,
  basePath,
  useDataItemDelivery,
  NoResultsHelp,
  urlRetrieveIds
} from "../hooks/api"
import { InternalLink, ReferenceLink } from "../components/helpersShared/linkHelpers"
import { WithData } from "../components/Loader"
import { withUrlQuery } from "../hooks/url-query"
import { AncestryData } from "../components/AncestryData"
import { Layout } from "../site-specific/Layout"
import { ShowJSON } from "../components/RawData"
import { AnalysisHistogram } from "../components/SVGloaders"
import { pluralizeWord }  from "../components/helpersShared/labelHelpers"

const itemColl = "biosamples"
// const exampleId = "pgxbs-kftvir6m"

const SampleDetailsPage = withUrlQuery(({ urlQuery }) => {
  var {id, datasetIds } = urlRetrieveIds(urlQuery)
  const iURL = `${basePath}beacon/biosamples/${id}/individuals?datasetIds=${datasetIds}&limit=1`
  var [individual, setIndividual] = useState([]);
  useEffect(() => {
    fetch( iURL )
       .then((response) => response.json())
       .then((data) => {
          console.log(data.response.resultSets[0].results[0]);
          setIndividual(data.response.resultSets[0].results[0])
       })
       .catch((err) => {
          console.log(err.message);
       });
   }, [setIndividual]);

  return (
    <Layout title="Sample Details">
      {id && datasetIds ? (
        <BiosampleLoader biosId={id} individual={individual} datasetIds={datasetIds} />
      ) : (
        NoResultsHelp(itemColl)
      )}
    </Layout>
  )
})

export default SampleDetailsPage

/*============================================================================*/
/*============================================================================*/
/*============================================================================*/

function BiosampleLoader({ biosId, individual, datasetIds }) {
  const apiReply = useDataItemDelivery(biosId, itemColl, datasetIds)

  return (
    <WithData
      apiReply={apiReply}
      background
      render={(response) => (
        <BiosampleResponse
          biosId={biosId}
          response={response}
          individual={individual} 
          datasetIds={datasetIds}
        />
      )}
    />
  )
}

/*============================================================================*/

function BiosampleResponse({ biosId, response, individual, datasetIds }) {
  if (!response.response.resultSets[0].results) {
    return NoResultsHelp(itemColl)
  }
  return <Biosample biosId={biosId} biosample={response.response.resultSets[0].results[0]} individual={individual} datasetIds={datasetIds} />
}

/*============================================================================*/

function Biosample({ biosId, biosample, individual, datasetIds }) {

  // console.log(individual);

  return (

<section className="content">

  <h2 className="mb-6">
    Sample Details for <i>{biosId}</i>
  </h2>

  {biosample.notes && (
    <>
      <h5>Description</h5>
      <p>{biosample.notes}</p>
    </>
  )}

  <h5>Diagnostic Classifications </h5>
  <ul>
  {BIOKEYS.map(bioc => (
    <li key={bioc}>
      {biosample[bioc].label}{": "}
      <InternalLink
        href={`/subset/?id=${biosample[bioc].id}&datasetIds=${ datasetIds }`}
        label={biosample[bioc].id}
      />
    </li>
  ))}      
  </ul>

  {/*------------------------------------------------------------------------*/}

  {biosample.celllineInfo && (
    <>
    <h5>Cell Line Info</h5>
    <ul>
    {biosample.celllineInfo.id && (
      <li>
        Instance of {" "}
        <InternalLink
          href={`/cellline/?id=${biosample.celllineInfo.id}&datasetIds=${ datasetIds }`}
          label={biosample.celllineInfo.id}
        />
      </li>
    )}
    </ul>
    </>
  )}


  {/*------------------------------------------------------------------------*/}


  <h5>Donor Details</h5>

  <ul>

 {individual?.description && (
    <li>
      <b>Description</b>{": "}
      {individual.description}
    </li>
  )}

  {individual?.indexDisease?.diseaseCode && (
    <li>
      <b>Diagnosis</b>{": "}
      {individual.indexDisease.diseaseCode.id}{" ("}
      {individual.indexDisease.diseaseCode?.label}{")"}
    </li>
      
  )}

  {individual?.description && (
    <li>
      <b>Description</b>{": "}
      {individual.description}
    </li>
  )}

  {individual?.sex && (
    <li>
      <b>Genotypic Sex</b>{": "}
      {individual?.sex?.label} ({individual.sex.id})
    </li>
  )}

  {individual?.indexDisease?.onset && (
      <li>
        <b>Age at Collection</b>{": "}
        {individual.indexDisease.onset.age}
      </li>
  )}

  </ul>

  {individual?.genomeAncestry && individual?.genomeAncestry?.length > 0 && (
    <>
      <h5>Genomic Ancestry</h5>
      <AncestryData individual={individual} />
    </>
  )}

  {/*------------------------------------------------------------------------*/}

  {biosample?.provenance && (
    <>
    <h5>Provenance</h5>
    <ul>
      {biosample.provenance?.material?.label && (
        <>
          <li>Material: {biosample.biosampleStatus.label}</li>
        </>
      )}
      {biosample.provenance?.geoLocation?.properties?.label && (
        <>
          <li>
            Origin: {biosample.provenance.geoLocation.properties.label}
          </li>
        </>
      )}
    </ul>
    </>
  )}

  {biosample.externalReferences && (
    <>
    <h5>External References</h5>
    <ul>
      {biosample.externalReferences.map((externalReference, i) => (
        <li key={i}>
          {externalReference.description && (
            `${externalReference.description}: `
          )}
          {externalReference.label && (
            `${externalReference.label}: `
          )}
          {ReferenceLink(externalReference) ? (
            <InternalLink
              href={ReferenceLink(externalReference)}
              label={`${externalReference.id}`}
            />
          ) : (
            externalReference.id
          )}
        </li>
      ))}
    </ul>
    </>
  )}

  { biosample.info && biosample.info?.callsetIds?.length > 0 && (
    <>
      <h5>CNV {pluralizeWord("Plot", biosample.info.callsetIds.length)}</h5>
      {biosample.info?.callsetIds.map((csid, i) => (
        <AnalysisHistogram key={i} csid={csid} datasetIds={datasetIds} />
      ))}
    </>
  )}

  <h5>Download</h5>
  <ul>
    <li>Sample data as{" "}
      <InternalLink
        href={`/beacon/biosamples/${biosId}`}
        label="Beacon JSON"
      />
    </li>
    <li>Sample data as{" "}
      <InternalLink
        href={`/beacon/biosamples/${biosId}/phenopackets`}
        label="Beacon Phenopacket JSON"
      />
    </li>
    <li>Sample variants as{" "}
      <InternalLink
        href={`/beacon/biosamples/${biosId}/genomicVariations`}
        label="Beacon JSON"
      />
    </li>
    <li>Sample variants as{" "}
      <InternalLink
        href={`/services/pgxsegvariants?biosample_ids=${biosId}`}
        label="Progenetix .pgxseg file"
      />
    </li>
    <li>Sample variants as{" "}
      <InternalLink
        href={`/services/vcfvariants?biosample_ids=${biosId}`}
        label="(experimental) VCF 4.4 file"
      />
    </li>
  </ul>

  <ShowJSON data={biosample} />

</section>
  )
}
