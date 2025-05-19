import { useAsyncSelect } from "../../hooks/asyncSelect"
import { useGeneSymbol } from "../../hooks/api"
import SelectField from "./SelectField"
import React from "react"

export function GeneSymbolSelector({
  name,
  label,
  control,
  errors,
  register,
  // className
}) {
  const { inputValue, onInputChange } = useAsyncSelect()
  const { data, isLoading } = useGeneSymbol({ geneId: inputValue })
  let options = []
  if (data) {
    options = data.response.results.map((g) => ({
      value: g.symbol,
      label: `${g.symbol} (chr${g.chromosome}:${g.start}-${g.end})`
    }))
  }
  return (
    <SelectField
      name={name}
      label={label}
      infoText="Start gene selection by typing a HUGO symbol..."
      isLoading={isLoading && !!inputValue}
      options={options}
      onInputChange={onInputChange}
      control={control}
      errors={errors}
      register={register}
      useOptionsAsValue
      isClearable
      isMulti
    />
  )
}
