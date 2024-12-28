import { useAsyncSelect } from "../../hooks/asyncSelect"
import { useGeoCity } from "../../hooks/api"
import SelectField from "../formShared/SelectField"
import React from "react"

export function GeoCitySelector({
  name,
  label,
  control,
  errors,
  register,
  className
}) {
  const { inputValue, onInputChange } = useAsyncSelect()
  const { data, isLoading } = useGeoCity({ city: inputValue })
  let options = []
  if (data) {
    if (data.response) {
      options = data.response.results.map((g) => ({
        value: g,
        data: g,
        label: `${g.geoLocation.properties.city} (${g.geoLocation.properties.country})`
      }))
    }
  }
  return (
    <SelectField
      name={name}
      label={label}
      infoText="Start city selection by typing a city name..."
      isLoading={isLoading && !!inputValue}
      options={options}
      onInputChange={onInputChange}
      control={control}
      errors={errors}
      register={register}
      className={className}
      useOptionsAsValue
      isClearable
    />
  )
}
