import {
  useDataItemDelivery,
  NoResultsHelp,
  urlRetrieveIds
} from "../hooks/api"
import { ReferenceLink, InternalLink, ExternalLink } from "../components/helpersShared/linkHelpers"
import { AncestryData } from "../components/AncestryData"
import { WithData } from "../components/Loader"
import { withUrlQuery } from "../hooks/url-query"
import { Layout } from "../site-specific/Layout"
import { ShowJSON } from "../components/RawData"

const itemColl = "individuals"
// const exampleId = "pgxind-kftx266l"

const IndividualDetailsPage = withUrlQuery(({ urlQuery }) => {
  const { id, datasetIds, hasAllParams } = urlRetrieveIds(urlQuery)
  return (
    <Layout title="Individual Details">
      {!hasAllParams ? (
        NoResultsHelp(itemColl)
      ) : (
        <IndividualLoader id={id} datasetIds={datasetIds} />
      )}
    </Layout>
  )
})

export default IndividualDetailsPage

function IndividualLoader({ id, datasetIds }) {
  const apiReply = useDataItemDelivery(id, itemColl, datasetIds)
  return (
    <WithData
      apiReply={apiReply}
      background
      render={(response) => (
        <IndividualResponse
          response={response}
          id={id}
          datasetIds={datasetIds}
        />
      )}
    />
  )
}

function IndividualResponse({ response, datasetIds }) {
  if (!response.response.resultSets[0].results) {
    return NoResultsHelp(itemColl)
  }
  return <Individual individual={response.response.resultSets[0].results[0]} datasetIds={datasetIds} />
}

function Individual({ individual, datasetIds }) {
  return (
    <section className="content">
      <h2 className="mb-6">
        Individual Details <i>{individual.id}</i>
      </h2>

     {individual.description && (
        <>
          <h5>Description</h5>
          <p>{individual.description}</p>
        </>
      )}

       {individual.sex && (
        <>
          <h5>Genotypic Sex</h5>
          <ul>
            <li>{individual.sex?.label} ({individual.sex.id})</li>
          </ul>
        </>
      )}

      {individual.onset &&
        <p>
          Age at Collection: {individual.onset?.age}
        </p>
      }

      {individual.diseaseCode &&
        <>
          <h5>Diagnosis</h5>
          <p>{individual.diseaseCode?.label}</p>
        </>
      }

      {individual.cellLines &&
        <>
        <h5>Cell Lines</h5>
        <ul>
        {individual.cellLines.map((cl, i) => (
          <li key={i}>
            {cl.description && (cl.description)}
            <ExternalLink
              href={ReferenceLink(cl)}
              label={`: ${cl.id}`}
            />
          </li>
        ))}
        </ul>
        </>
      }

      {individual?.genomeAncestry && individual?.genomeAncestry?.length > 0 && (
        <>
          <h5>Genomic Ancestry</h5>
          <AncestryData individual={individual} />
        </>
      )}

      {individual.biosamples && individual.biosamples.length > 0 &&
        <>
        <h5>Biosamples</h5>
        {individual.biosamples.map((bs, i) => (
          <li key={i}>
          <InternalLink
            href={`/biosample/?id=${bs}&datasetIds=${ datasetIds }`}
            label={bs}
          />
          </li>
        ))}
        </>
      }
      
      <h5>Download</h5>
      <ul>
        <li>Subject data as{" "}
          <InternalLink
            href={`/beacon/individuals/${individual.id}`}
            label="Beacon JSON"
          />
        </li>
        <li>Sample data as{" "}
          <InternalLink
            href={`/beacon/individuals/${individual.id}/phenopackets`}
            label="Beacon Phenopacket JSON"
          />
        </li>
        <li>Variants as{" "}
          <InternalLink
            href={`/beacon/individuals/${individual.id}/genomicVariations`}
            label="Beacon JSON"
          />
        </li>
        <li>Variants as{" "}
          <InternalLink
            href={`/services/pgxsegvariants?individual_ids=${individual.id}`}
            label="Progenetix .pgxseg file"
          />
        </li>
        <li>Variants as{" "}
          <InternalLink
            href={`/services/vcfvariants?individual_ids=${individual.id}`}
            label="(experimental) VCF 4.4 file"
          />
        </li>
      </ul>

      <ShowJSON data={individual} />

    </section>
  )
}

