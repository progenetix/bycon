import { useProgenetixApi, basePath } from "../../hooks/api"
import { useEffect, useState } from "react"
import { keyBy } from "lodash"

export function GeneLabelOptions(inputValue) {
  const { data, isLoading } = useGeneSpans(inputValue)
  const [cachedGenes, setCachedGenes] = useState({})
  useEffect(() => {
    if (data) {
      const genes = keyBy(data.response.results, "symbol")
      setCachedGenes({ ...genes, ...cachedGenes })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])
  const options = Object.entries(cachedGenes).map(([, gene]) => {
    return {
      value: gene.symbol,
      label: geneLabel(gene)
    }
  })
  return { isLoading, options }
}

export function useGeneSpanSelect(inputValue) {
  const { data, error, isLoading } = useGeneSpans(inputValue)
  let options = []
  if (data) {
    options = data.response.results.map((gene) => ({
      value: gene,
      label: labeledGeneSpan(gene)
    }))
  }
  return { isLoading, error, options }
}

function useGeneSpans(querytext) {
  const url = querytext && querytext.length > 0 && geneSearchUrl(querytext)
  return useProgenetixApi(url, (...args) =>
    fetch(...args)
      .then((res) => res.text())
      .then((t) => {
        // apiReply returned is not JSON
        return JSON.parse(t)
      })
  )
}

function labeledGeneSpan(gene) {
  return (
    gene.referenceName +
    ":" +
    gene.start +
    "-" +
    gene.end +
    ":" +
    gene.symbol
  )
}

function geneLabel(gene) {
  return (
    gene.symbol +
    " (" +
    gene.referenceName +
    ":" +
    gene.start +
    "-" +
    gene.end +
    ")"
  )
}

function geneSearchUrl(querytext) {
  return `${basePath}services/genespans/?geneId=${querytext}&filterPrecision=start&deliveryKeys=symbol,referenceName,start,end`
}
