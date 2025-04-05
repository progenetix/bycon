import { FaExternalLinkAlt, FaLink } from "react-icons/fa"


export function InternalLink({ href, label, onClick }) {
  return (
    <a href={href} onClick={onClick}>
      {label} <FaLink className="icon has-text-grey-light is-small" />
    </a>
  )
}

export function ExternalLink({ href, label, onClick }) {
  return (
    <a href={href} rel="noreferrer" target="_blank" onClick={onClick}>
      {label} <FaExternalLinkAlt className="icon has-text-info is-small" />
    </a>
  )
}

// TODO: This cries for a template / yaml ... and a better name
export function ReferenceLink(externalReference) {
  if (externalReference.id.includes("cellosaurus:")) {
    return (
      "https://www.cellosaurus.org/" +
      externalReference.id.replace("cellosaurus:", "")
    )
  } else if (externalReference.id.includes("pubmed:")) {
    return "/publication/?id=" + externalReference.id
  } else if (externalReference.id.includes("geo:")) {
    return (
      "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=" +
      externalReference.id.replace("geo:", "")
    )
  } else if (externalReference.id.includes("arrayexpress:")) {
    return (
      "https://www.ebi.ac.uk/arrayexpress/experiments/" +
      externalReference.id.replace("arrayexpress:", "")
    )
  } else if (externalReference.id.includes("cbioportal")) {
    return (
      "https://www.cbioportal.org/study/summary?id=" +
      externalReference.id.replace("cbioportal:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("TCGA-")) {
    return (
      "https://portal.gdc.cancer.gov/projects/" +
      externalReference.id.replace("pgx:", "")
    )
  } else if (externalReference.id.includes("biosample")) {
    return (
      "https://www.ebi.ac.uk/biosamples/samples/" +
      externalReference.id.replace("biosample:", "")
    )
  } else if (externalReference.id.includes("MedGen")) {
    return (
      "https://www.ncbi.nlm.nih.gov/medgen/" +
      externalReference.id.replace("MedGen:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("MONDO")) {
    return (
      "https://monarchinitiative.org/disease/MONDO:" +
      externalReference.id.replace("MONDO:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("OMIM")) {
    return (
      "https://omim.org/clinicalSynopsis/" +
      externalReference.id.replace("OMIM:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("Orphanet")) {
    return (
      "https://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=EN&Expert=" +
      externalReference.id.replace("Orphanet:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("MeSH")) {
    return (
      "https://www.ncbi.nlm.nih.gov/mesh/?term=" +
      externalReference.id.replace("MeSH:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("HP")) {
    return (
      "https://hpo.jax.org/app/browse/term/" +
      externalReference.id.replace("Human Phenotype Ontology:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("SNOMED CT")) {
    return (
      "https://snomedbrowser.com/Codes/Details/" +
      externalReference.id.replace("SNOMED CT:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("dbSNP")) {
    return (
      "https://www.ncbi.nlm.nih.gov/snp/rs" +
      externalReference.id.replace("dbSNP:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("ClinGen")) {
    return (
      "http://reg.clinicalgenome.org/redmine/projects/registry/genboree_registry/by_caid?caid=" +
      externalReference.id.replace("ClinGen:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("ClinVar")) {
    return (
      "https://www.ncbi.nlm.nih.gov/clinvar/variation/" +
      externalReference.id.replace("ClinVar:", "").toLowerCase()
    )
  } else if (externalReference.id.includes("HGNC")) {
    return (
      "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/" +
      externalReference.id.replace("HGNC:", "").toLowerCase()
    )
  } else {
    return null
  }
}

export function epmcId(publicationId) {
  return publicationId.split(":")[1]
}

export function epmcUrl(publicationId) {
  return `http://www.europepmc.org/abstract/MED/${epmcId(publicationId)}`
}

export function EpmcLink({ publicationId }) {
  return (
    <a href={epmcUrl(publicationId)} rel="noreferrer" target="_BLANK">
      <img src="/img/icon_EPMC_16.gif" />
    </a>
  )
}
