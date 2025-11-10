import React, { useRef, useState } from "react"
import {
  getVisualizationLink,
  replaceWithProxy,
  useProgenetixApi,
  useExtendedSWR
} from "../../hooks/api"
import cn from "classnames"
import BiosamplesDataTable from "./BiosamplesDataTable"
import VariantsDataTable from "./VariantsDataTable"
import { useContainerDimensions } from "../../hooks/containerDimensions"
import SVGloader from "../SVGloaders"
import { ExternalLink } from "../helpersShared/linkHelpers"
import { svgFetcher } from "../../hooks/fetcher"
import BiosamplesStatsDataTable from "./BiosamplesStatsDataTable"
import { WithData } from "../Loader"
import { refseq2chro } from "../Chromosome"
import { AggregatedPlots } from "../AggregatedPlots"

const HANDOVER_IDS = {
  histoplot: "histoplot",
  biosamples: "biosamples",
  biosamplestable: "biosamplestable",
  biosamplesmap: "biosamplesmap",
  phenopackets: "phenopackets",
  UCSClink: "UCSClink",
  variants: "variants",
  pgxseg: "pgxseg",
  vcf: "vcf"
}

const TABS = {
  results: "Results",
  samples: "Biosamples",
  samplesMap: "Biosamples Map",
  variants: "Variants"
}

export function DatasetResultBox({ data: responseSet, responseMeta, query }) {
  const {
    id,
    resultsHandovers,
    info,
    summaryResults,
    resultsCount
  } = responseSet

  // TODO: This is ugly; something like := ?
  const limit = responseMeta.receivedRequestSummary?.pagination?.limit ? responseMeta.receivedRequestSummary?.pagination?.limit : 200

  const handoverById = (givenId) =>
    resultsHandovers.find(({ info: { contentId } }) => contentId === givenId)

  // obviously should be looped somehow...
  const biosamplesHandover = handoverById(HANDOVER_IDS.biosamples)
  const biosamplesTableHandover = handoverById(HANDOVER_IDS.biosamplestable)
  const biocount = biosamplesHandover?.info?.count ? biosamplesHandover.info.count : 0
  biosamplesHandover.pages = []
  biosamplesTableHandover.pages = []
  var cntr = 0
  var skpr = 0
  if (biocount > 0) {
    while (cntr < biocount) {
      const pagu = "&skip=" + skpr + "&limit=" + limit
      cntr += limit
      skpr += 1
      biosamplesHandover.pages.push({"url": replaceWithProxy(biosamplesHandover.url + pagu), "label": "Part" + skpr})
      biosamplesTableHandover.pages.push({"url": replaceWithProxy(biosamplesTableHandover.url + pagu), "label": "Part" + skpr})
    }
  }

  const variantsHandover = handoverById(HANDOVER_IDS.variants)
  const vcfHandover = handoverById(HANDOVER_IDS.vcf)
  const pgxsegHandover = handoverById(HANDOVER_IDS.pgxseg)
  const varcount = variantsHandover?.info?.count ? variantsHandover.info.count : 0
  // variants are optional and existence has to be checked at several places
  if (varcount > 0) {
    variantsHandover.pages = []
    vcfHandover.pages = []
    pgxsegHandover.pages = []
    cntr = 0
    skpr = 0
    while (cntr < varcount) {
      const pagu = "&skip=" + skpr + "&limit=" + limit
      cntr += limit
      skpr += 1
      variantsHandover.pages.push({"url": replaceWithProxy(variantsHandover.url + pagu), "label": "Part" + skpr})
      vcfHandover.pages.push({"url": replaceWithProxy(vcfHandover.url + pagu), "label": "Part" + skpr})
      pgxsegHandover.pages.push({"url": replaceWithProxy(pgxsegHandover.url + pagu), "label": "Part" + skpr})
    }
  }

  // const phenopacketsHandover = handoverById(HANDOVER_IDS.phenopackets)
  const UCSCbedHandoverURL = handoverById(HANDOVER_IDS.UCSClink) === undefined ? false : handoverById(HANDOVER_IDS.UCSClink).url
  const biosamplesmapURL = handoverById(HANDOVER_IDS.biosamplesmap) === undefined ? false : handoverById(HANDOVER_IDS.biosamplesmap).url

  // Data retrieval; variants are optional and existence has to be checked at several places
  const variantsReply = useProgenetixApi(varcount > 0 ? variantsHandover.pages[0].url : "")
  const biosamplesReply = useProgenetixApi(biosamplesHandover.pages[0].url)
  const retrievedSampleCount = biosamplesReply?.data?.response?.resultSets[0]?.results.length

  // the histogram is only rendered but correct handover is needed, obviously
  let histoplotUrl
  let visualizationLink
  if (handoverById(HANDOVER_IDS.histoplot)) {
    histoplotUrl = handoverById(HANDOVER_IDS.histoplot).url + "&limit=" + limit
    let visualizationAccessId = new URLSearchParams(
      new URL(histoplotUrl).search
    ).get("accessid")
    visualizationLink = getVisualizationLink(id, visualizationAccessId, "", 0, limit, resultsCount)
  }

  // main / samples / variants
  const tabNames = [TABS.results]
  biocount > 0 && tabNames.push(TABS.samples)
  varcount > 0 && tabNames.push(TABS.variants)
  const [selectedTab, setSelectedTab] = useState(tabNames[0])

  let tabComponent
  if (selectedTab === TABS.results) {
    tabComponent = (
      <ResultsTab
        variantType={query.alternateBases}
        histoplotUrl={histoplotUrl}
        biosamplesReply={biosamplesReply}
        variantCount={info.counts.variants}
        datasetId={id}
      />
    )
  } else if (selectedTab === TABS.samples) {
    tabComponent = (
      <BiosamplesDataTable apiReply={biosamplesReply} datasetId={id} />
    )
  // } else if (selectedTab === TABS.samplesMap) {
  //   tabComponent = (
  //     <div>
  //       <h2 className="subtitle has-text-dark">Sample Origins</h2>
  //       <p>
  //         The map represents the origins of the matched samples, as derived from
  //         the original publication or resource repository. In the majority of
  //         cases this will correspond to the proxy information of the
  //         corresponding author&apos;s institution. Additional information can be
  //         found in the{" "}
  //         <ExternalLink
  //           href={`${SITE_DEFAULTS.MASTERDOCLINK}/geolocations.html`}
  //           label="Geographic Coordinates documentation"
  //         />
  //         {"."}
  //       </p>
  //       {/*<BiosamplesMap apiReply={biosamplesReply} datasetId={id} />*/}
  //     </div>
  //   )
  } else if (selectedTab === TABS.variants) {
    tabComponent = (
      <VariantsDataTable apiReply={variantsReply} datasetId={id} />
    )
  }

  return (
    <div className="box">
      <h2 className="subtitle has-text-dark">{id}</h2>
      <div className="columns">
        <div className="column is-one-third">
          <div>
            <b>Matched Samples: </b>
            {resultsCount}
          </div>
          <div>
            <b>Retrieved Samples: </b>
            {retrievedSampleCount}
          </div>
          {info.counts.variants > 0 ? (
            <div>
              <div>
                <b>Variants: </b>
                {info.counts.variants}
              </div>
              <div>
                <b>Calls: </b>
                {info.counts.analyses}
              </div>
            </div>
          ) : null}
        </div>
        <div className="column is-one-third">
          {info.counts.variants > 0 && query?.referenceName ? (
            <div>
              <UCSCRegion query={query} />
            </div>
          ) : null}
          {biosamplesmapURL ? (
            <div>
              <ExternalLink
                label="Geographic Map"
                href={biosamplesmapURL}
              />
            </div>
          ) : null}
          {info.counts.variants > 0 ? (
            <div>
              <ExternalLink
                label="Variants in UCSC"
                href={UCSCbedHandoverURL}
              />
            </div>
          ) : null}
          <div>
            <ExternalLink
              label="Dataset Responses (JSON)"
              onClick={() => openJsonInNewTab(responseSet)}
            />
          </div>
        </div>
        {visualizationLink && (
          <div className="column is-one-third">
            <a className="button is-info mb-5" href={visualizationLink}>
              Visualization options
            </a>
          </div>
        )}
      </div>
      {tabNames?.length > 0 ? (
        <div className="tabs is-boxed ">
          <ul>
            {tabNames.map((tabName, i) => (
              <li
                className={cn({
                  "is-active": selectedTab === tabName
                })}
                key={i}
                onClick={() => setSelectedTab(tabName)}
              >
                <a>{tabName}</a>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {tabComponent ? <div>{tabComponent}</div> : null}

      <br/>
      <AggregatedPlots summaryResults={summaryResults} />
      <br/>
      <hr/>
      <h2 className="subtitle has-text-dark">{id} Data Downloads</h2>

      {biosamplesTableHandover?.pages.length > 0 && (
        <div className="tabs">
          <div>
            <b>Download Sample Data (TSV)</b>
            <br/>
            <ul>
              {biosamplesTableHandover.pages.map((handover, i) => (
                <PagedLink key={i} handover={handover} />
              ))}
            </ul>
          </div>
        </div>
      )}
      {biosamplesHandover?.pages.length > 0 && (
        <div className="tabs">
          <div>
            <b>Download Sample Data (JSON)</b>
            <br/>
            <ul>
              {biosamplesHandover.pages.map((handover, i) => (
                <PagedLink key={i} handover={handover} />
              ))}
            </ul>
          </div>
        </div>
      )}
      {variantsHandover?.pages.length > 0 && (
        <div className="tabs ">
          <div>
            <b>Download Variants (Beacon VRS)</b>
            <br/>
            <ul>
              {variantsHandover?.pages.map((handover, i) => (
                <PagedLink key={i} handover={handover} />
              ))}
            </ul>
          </div>
        </div>
      )}
      {vcfHandover?.pages.length > 0 && (
        <div className="tabs ">
          <div>
            <b>Download Variants (VCF)</b>
            <br/>
            <ul>
              {vcfHandover?.pages.map((handover, i) => (
                <PagedLink key={i} handover={handover} />
              ))}
            </ul>
          </div>
        </div>
      )}
      {pgxsegHandover?.pages.length > 0 && (
        <div className="tabs ">
          <div>
            <b>Download Variants (.pgxseg)</b>
            <br/>
            <ul>
              {pgxsegHandover?.pages.map((handover, i) => (
                <PagedLink key={i} handover={handover} />
              ))}
            </ul>
          </div>
        </div>
      )}
{/* 
      {phenopacketsHandover?.pages && (
        <div className="tabs">
          <div>
            <b>Download Phenopackets (JSON)</b>
            <br/>
            <ul>
              {phenopacketsHandover.pages.map((handover, i) => (
                <PagedLink key={i} handover={handover} />
              ))}
            </ul>
          </div>
        </div>
      )}
*/}    
    </div>
  )
}

function ResultsTab({
  histoplotUrl,
  biosamplesReply,
  variantCount,
  datasetId
}) {
  return (
    <div>
      {histoplotUrl && (
        <div className="mb-4">
          <CnvHistogramPreview url={histoplotUrl} />
          <ExternalLink href={histoplotUrl} label="Reload histogram in new window" />
        </div>
      )}
      <WithData
        apiReply={biosamplesReply}
        background
        render={(biosamplesResponse) => (
          <BiosamplesStatsDataTable
            biosamplesResponse={biosamplesResponse}
            variantCount={variantCount}
            datasetId={datasetId}
          />
        )}
      />
    </div>
  )
}

function CnvHistogramPreview({ url: urlString }) {
  const url = new URL(urlString)
  const componentRef = useRef()
  const { width } = useContainerDimensions(componentRef)
  url.search = new URLSearchParams([
    ...url.searchParams.entries(),
    // ["plotPars=plot_width", width]
  ]).toString() + "&plotPars=plot_width=" + width
  let withoutOrigin = replaceWithProxy(url)
  // width > 0 to make sure the component is mounted and avoid double fetch
  const dataEffect = useExtendedSWR(width > 0 && withoutOrigin, svgFetcher)
  return (
    <div ref={componentRef}>
      <SVGloader apiReply={dataEffect} />
    </div>
  )
}

function UCSCRegion({ query }) {
  return <ExternalLink href={ucscHref(query)} label=" UCSC region" />
}

function ucscHref(query) {

  let ucscpos = query.start + "," + query.end
  ucscpos = ucscpos.split(",").filter(Number)
  let start = Math.min.apply(Math, ucscpos)
  let end = Math.max.apply(Math, ucscpos)
  let chro = refseq2chro(query.referenceName)

  return `http://www.genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=chr${chro}%3A${start}%2D${end}`
}

function PagedLink({ handover }) {
  return (
    <li>
      <ExternalLink
        href={handover.url}
        label={handover.label}
        download
      />
    </li>
  )
}

function openJsonInNewTab(dataJson) {
  const jsonString = JSON.stringify(dataJson, null, 2)
  const x = window.open()
  x.document.open()
  x.document.write(`<html><body><pre>${jsonString}</pre></body></html>`)
  x.document.close()
}

// const BiosamplesMap = dynamic(() => import("./BioSamplesMap"), {
//   ssr: false
// })
