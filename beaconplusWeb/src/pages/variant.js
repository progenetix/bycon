import {
  getDataItemUrl,
  useDataItemDelivery,
  NoResultsHelp,
  urlRetrieveIds
} from "../hooks/api"
import { ExternalLink, ReferenceLink } from "../components/helpersShared/linkHelpers"
import { WithData } from "../components/Loader"
import { withUrlQuery } from "../hooks/url-query"
import { Layout } from "../site-specific/Layout"
import { ShowJSON } from "../components/RawData"
import { BiosamplePlot } from "../components/SVGloaders"
import React from "react"
import { refseq2chro } from "../components/Chromosome"

const entity = "variants"
// const exampleId = "pgxvar-5bab576a727983b2e00b8d32"

const VariantDetailsPage = withUrlQuery(({ urlQuery }) => {
  const { id, datasetIds, hasAllParams } = urlRetrieveIds(urlQuery)
  return (
    <Layout title="Variant Details" headline="Variant Details">
      {!hasAllParams ? (
        NoResultsHelp(entity)
      ) : (
        <VariantLoader id={id} datasetIds={datasetIds} />
      )}
    </Layout>
  )
})

export default VariantDetailsPage

function VariantLoader({ id, datasetIds }) {
  const apiReply = useDataItemDelivery(id, entity, datasetIds)
  return (
    <WithData
      apiReply={apiReply}
      background
      render={(response) => (
        // <>
          <VariantResponse
            response={response}
            id={id}
            datasetIds={datasetIds}
          />
      )}
    />
  )
}

function VariantResponse({ response, id, datasetIds }) {
  if (!response.response.resultSets[0].results[0]) {
    return NoResultsHelp(entity)
  }
  return (
    <Variant
      variant={response.response.resultSets[0].results[0]}
      id={id}
      datasetIds={datasetIds}
   />)
}

function Variant({ variant, id, datasetIds }) {
  // TODO: add variatrion type or sequence from VRS response

  const v = variant.variation ? variant.variation : false
  console.log(v)
  var locations = []
  var chros = []
  var markers = []
  if (v.subject) {
    locations.push(v.subject)
  } else if (v.location) {
    locations.push(v.location)
  } else if (v.adjoinedSequences) {
    locations.push(...v.adjoinedSequences)
  }

  console.log(locations)

  locations.forEach(function (loc) {
    if (loc.sequenceReference) {
      const chro = refseq2chro(loc.sequenceReference)
      chros.push(chro)
      var start = 0
      var end = 1
      // TODO: This is a slightly ugly deparsing of the "evolving" VRS v2 options
      if (loc.start && loc.end) {
        start = loc.start
        end = loc.end
      } else if (loc.start) {
        start = loc.start[0]
        end = loc.start[1]
      } else if (loc.end) {
        start = loc.end[0]
        end = loc.end[1]
      }
      const m = chro + ":" + start + "-" + end
      const l = "chr" + chro + " (" + start + "-" + end + ")"
      markers.push(m + ":" + l)
    }
  });

  console.log(markers)

  return (
    <section className="content">
      <h3>
        {id} ({datasetIds})
      </h3>

      <h5>Digest</h5>
      <p>{variant.variantInternalId}</p>
      {v?.molecularAttributes && (
        <>
          <h5>Molecular Attributes</h5>
          <ul>
          {v.molecularAttributes.geneIds && (
            <li>Gene: <b>{v.molecularAttributes.geneIds[0]}</b></li>
          )}
          {v.molecularAttributes?.molecularEffects && (
            <li>Molecular effect: {v.molecularAttributes.molecularEffects[0].label}</li>
          )}
          {v.molecularAttributes.aminoacidChanges && v.molecularAttributes.aminoacidChanges.length > 0 && variant.variation.molecularAttributes.aminoacidChanges[0] !== null && (
              <li>Aminoacid changes:
                <ul>
                  {v.molecularAttributes.aminoacidChanges.map((aa) => (
                      <li key={aa}>
                        {aa}
                      </li>
                  ))}
                </ul>
              </li>
            )}
          </ul>
        </>
      )}

      {v?.identifiers && (
        <>
        <h5>Variant Identifiers</h5>
        <ul>
        {v.identifiers?.proteinHGVSIds && (
          <li>Protein HGVSids:
            <ul>
            {v.identifiers.proteinHGVSIds.map((ph) =>
              <li key={ph}>
                {ph}
              </li>
            )}
            </ul>
          </li>
        )}

        {v.identifiers?.genomicHGVSIds && (
          <li>Genomic HGVSids:
            <ul>
            {variant.variation.identifiers.genomicHGVSIds.map((gh) =>
              <li key={gh}>
                {gh}
              </li>
            )}
            </ul>
          </li>
        )}

        {v.identifiers?.clinvarIds && (
            <li>ClinVar IDs:
              <ul>
                <li>
                  <ExternalLink
                    href={`http://www.ncbi.nlm.nih.gov/clinvar/variation/${variant.variation.identifiers.clinvarIds[0]}`}
                    label={v.identifiers.clinvarIds[1]}
                  />
                </li>
              </ul>
            </li>
        )}

        </ul>
        </>
      )}

      {v?.variantAlternativeIds && (
        <div>
          <h5>Variant Alternative IDs</h5>
          <ul>
            {v.variantAlternativeIds.map((altid, key) => (
                <li key={key}>
                  {altid.id} - {altid.label}
                </li>
            ))}
          </ul>
        </div>
      )}

      {v?.variantLevelData?.clinicalInterpretations && (
        <>
        {v.variantLevelData && variant.variation.variantLevelData.clinicalInterpretations.length > 0 && (
          <>
          <h5>Clinical Interpretations</h5>
          <p>Clinical Relevance: <b>{v.variantLevelData.clinicalInterpretations[0].clinicalRelevance}</b></p>
          <table>
            <tr>
              <th>ID</th>
              <th>Description</th>
            </tr>
            {v.variantLevelData.clinicalInterpretations?.map((clinicalInterpretations, key) => {
              return (
                <tr key={key}>
                  <td>
                  {ReferenceLink(clinicalInterpretations.effect) ? (
                    <ExternalLink
                      href={ReferenceLink(clinicalInterpretations.effect)}
                      label={clinicalInterpretations.effect.id}
                    />
                  ) : (
                    clinicalInterpretations.effect.id
                  )}
                  </td>
                  <td>{clinicalInterpretations.effect.label}</td>
                </tr>
              )
              })}
          </table>
          </>
        )}
        </>
      )}

      <h5>
        Download Data as Beacon v2{" "}
        <a
          rel="noreferrer"
          target="_blank"
          href={getDataItemUrl(id, entity, datasetIds)}
        >
          {"{JSON↗}"}
        </a>
      </h5>

      <ShowJSON data={variant} />

      {variant.caseLevelData[0]?.biosampleId && (
        <>
          <h5>Plot</h5>
          <BiosamplePlot biosid={variant.caseLevelData[0].biosampleId} datasetIds={datasetIds} plotRegionLabels={markers.join(",")} plotChros={chros.join(",")} />
        </>
      )}

    </section>
  )
}
