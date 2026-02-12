import { ontologymapsUrl, useProgenetixApi } from "../hooks/api"
import Link from "next/link"

export function CodeGroups({ codeGroups, ontomapsUrl }) {
  return (
    <div className="content">
      <h5>
        Matching Code Mappings{" "}
        <a rel="noreferrer" target="_blank" href={ontomapsUrl}>
          {"{JSON↗}"}
        </a>
      </h5>
      <table className="table is-bordered">
        <tbody>
          {codeGroups.map((codeGroup, i) => (
            <tr key={i}>
              {codeGroup.map((code) => (
                <td key={code.id}>
                  <Link
                    href={`/subset/?datasetIds=progenetix&id=${code.id}`}
                  >
                    <a>{code.id}</a>
                  </Link>
                  {": "}
                  {code.label}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {codeGroups.length > 1 && (
        <p>
          More than one code groups means that either mappings need refinements
          (e.g. additional specific NCIT classes for ICD-O T topographies) or
          you started out with an unspecific ICD-O M class and need to add a
          second selection.
        </p>
      )}
    </div>
  )
}

export function useOntologymaps({ filters, filterPrecision }) {
  const url =
    filters?.length > 0 && ontologymapsUrl({ filters, filterPrecision })
  return useProgenetixApi(url)
}

export function useGetFilteredOptions({
  filters,
  filterResult,
  filterPrecision
}) {
  const { data, isLoading, error } = useOntologymaps({
    filters,
    filterPrecision
  })

  let options = mapToOptions(data)
  options = filterResult
    ? options.filter((o) => o.value !== filterResult)
    : options
  return { isLoading, error, options }
}

function mapToOptions(data) {
  if (!data || data.response.results[0].uniqueTerms == null) return []
  const ut = data.response.results[0].uniqueTerms
  const NCITneoplasm = filterTermlistByPrefix("NCIT", ut) ?? []
  const icdom = filterTermlistByPrefix("pgx:icdom", ut) ?? []
  const icdot = filterTermlistByPrefix("pgx:icdot", ut) ?? []
  const UBERON = filterTermlistByPrefix("UBERON", ut) ?? []
  return [NCITneoplasm, icdom, icdot, UBERON].flat().map((c) => ({
    label: c.id + ": " + c.label,
    value: c.id
  }))
}

function filterTermlistByPrefix(prefix, ut) {
  console.log(prefix)
  var re = new RegExp(prefix, "g")
  return ut.filter(function (el) {
    return el.id.match(re)
  })
}
