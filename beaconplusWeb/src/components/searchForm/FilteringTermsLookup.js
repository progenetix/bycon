// import { useFiltersByType } from "../../hooks/api"


// export default function FilteringTermsLookup(watchForm, ct, parameterKey) {
//   const datasetIds = watchForm("datasetIds");
//   const { data, isLoading } = useFiltersByType({
//     datasetIds,
//     collationTypes: ct
//   });

//   const options = data?.response?.filteringTerms?.map(value => ({
//     value: value.id,
//     label: `${value.id}: ${value.label} (${value.count})`
//   }));

//   return { options }
// )