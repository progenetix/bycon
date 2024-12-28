import { Chromosome, refseq2chro } from "../Chromosome"
import { Cytobands } from "../Cytobands"
import React, { useRef } from "react"
import { useContainerDimensions } from "../../hooks/containerDimensions"

export default function ChromosomePreview({ watch }) {
  const componentRef = useRef()
  const cytoBands = Cytobands()
  const { width } = useContainerDimensions(componentRef)
  const startRange = watch("start")
  const endRange = watch("end")
  const mateStartRange = watch("mateStart")
  const mateEndRange = watch("mateEnd")
  const referenceName = watch("referenceName")
  const mateName = watch("mateName")
  const chro = referenceName ? refseq2chro(referenceName) : ""
  const mateChro = mateName ? refseq2chro(mateName) : ""
  const bands = cytoBands["chr" + chro]
  const mateBands = cytoBands["chr" + mateChro]
  const shouldDisplay = (startRange || endRange) && bands
  const shouldDisplayMate = (mateStartRange || mateEndRange) && mateBands

  return (
    <div ref={componentRef}>
      {shouldDisplay && (
        <Chromosome
          bands={bands}
          refseqId={referenceName}
          startRange={startRange}
          endRange={endRange}
          width={width}
        />
      )}
      {shouldDisplayMate && (
        <Chromosome
          bands={mateBands}
          refseqId={mateName}
          startRange={mateStartRange}
          endRange={mateEndRange}
          width={width}
        />
      )}
    </div>
  )
}
