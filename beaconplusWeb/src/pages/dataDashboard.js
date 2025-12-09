import React from "react"
import Panel from "./../components/Panel"
import { AggregatedPlots } from "./../components/AggregatedPlots"
import {Layout} from "./../site-specific/Layout"
import { DATASETDEFAULT, tryFetch, THISSITE } from "./../hooks/api"

// http://beaconplus.org/stats/?datasetIds=progenetix&ageSplits=P0D,P1Y,P2Y,P18Y,P21Y,P40Y

export default function StatsPage({summaryResults, counts}) {


  const title = `${DATASETDEFAULT} Data Content Overview`
  const leadText = `This page shows some data statistics for the ${DATASETDEFAULT}
dataset. Please allow for some loading time.`

  return (
<Layout title={title} headline={title} leadPanelMarkdown={leadText}>
  <Panel heading="Dataset Summary">
    <ul>
      <li>Variants: {counts.genomicVariant}</li>
      <li>Analyses: {counts.analysis}</li>
      <li>Biosamples: {counts.biosample}</li>
      <li>Individuals: {counts.individual}</li>
    </ul>
  </Panel>
  <Panel heading="Some Content Statistics">
    <AggregatedPlots
      summaryResults={summaryResults}
      filterUnknowns={true}
    />
  </Panel>
</Layout>
  )
}

export const getStaticProps = async () => {
  const aggregationReply = await tryFetch(
    `${THISSITE}beacon/datasets/${DATASETDEFAULT}?requestedGranularity=aggregated`
  )

  return {
    props: {
      summaryResults: aggregationReply.response.collections[0].summaryResults,
      counts: aggregationReply.response.collections[0].counts
    }
  }
}
