import { Loader } from "./Loader"
import React, { useRef } from "react"
import {
  basePath,
  useSubsethistogram,
  subsetHistoBaseLink,
  subsetIdLink,
  subsetPgxsegLink,
  useExtendedSWR
} from "../hooks/api"
import { svgFetcher } from "../hooks/fetcher"
import { useContainerDimensions } from "../hooks/containerDimensions"
import PropTypes from "prop-types"
import Link from "next/link"

export default function SVGloader({ apiReply }) {
  const { data, error, isLoading } = apiReply
  return (
    <Loader isLoading={isLoading} hasError={error} background>
      <div
        className="svg-container"
        dangerouslySetInnerHTML={{ __html: data }}
      />
    </Loader>
  )
}

export function SubsetHistogram({
  id,
  datasetIds,
  fileId,
  plotRegionLabels,
  plotGeneSymbols,
  plotCytoregionLabels,
  title,
  description,
  size: givenSize 
}) {
  const componentRef = useRef()
  const { width } = useContainerDimensions(componentRef)
  const size = givenSize || width
  return (
    <div ref={componentRef}>
      <SVGloader
        apiReply={useSubsethistogram({
          datasetIds,
          id,
          fileId,
          plotRegionLabels,
          plotGeneSymbols,
          plotCytoregionLabels,
          size
        })}
      />
      <div className="img-legend">
      {title && (
        <>      
          <b>{title}</b>
        </>
      )}
      {description && (
        <>      
          {" "}{description}
        </>
      )}
      </div>
      <div className="svg-histolinks">
        <Link href={subsetHistoBaseLink(id, datasetIds)}>
          <a>Download SVG</a>
        </Link>
        {" | "}
        <Link href={subsetIdLink(id)}>
          <a>Go to {id}</a>
        </Link>
        {" | "}
        <Link href={subsetPgxsegLink(id)}>
          <a>Download CNV Frequencies</a>
        </Link>
      </div>
    </div>
  )
}

export function AnalysisHistogram({ csid, datasetIds }) {
  const componentRef = useRef()
  const { width } = useContainerDimensions(componentRef)
  const url = `${basePath}services/sampleplots?plotType=samplesplot&analysisIds=${csid}&datasetIds=${datasetIds}&plot_width=${width}`
  // width > 0 to make sure the component is mounted and avoid double fetch
  const dataEffect = useExtendedSWR(width > 0 && url, svgFetcher)
  return (
    <div ref={componentRef} className="mb-4">
      <SVGloader apiReply={dataEffect} />
    </div>
  )
}

export function BiosamplePlot({ biosid, datasetIds, plotRegionLabels, plotChros}) {
  const componentRef = useRef()
  const { width } = useContainerDimensions(componentRef)
  const url = `${basePath}services/sampleplots/${biosid}?plotType=samplesplot&datasetIds=${datasetIds}&plotPars=plot_width=${width}::plotRegionLabels=${plotRegionLabels}::plotChros=${plotChros}::forceEmptyPlot=true`
  // width > 0 to make sure the component is mounted and avoid double fetch
  const dataEffect = useExtendedSWR(width > 0 && url, svgFetcher)
  return (
    <div ref={componentRef} className="mb-4">
      <SVGloader apiReply={dataEffect} />
    </div>
  )
}

SubsetHistogram.propTypes = {
  id: PropTypes.string.isRequired,
  background: PropTypes.bool
}
