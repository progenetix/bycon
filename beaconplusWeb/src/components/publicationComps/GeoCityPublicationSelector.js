import React, { useEffect } from "react"
import { useAsyncSelect } from "../../hooks/asyncSelect"
import CustomSelect from "../Select"
import { useGeoCity } from "../../hooks/api"

export default function GeoCityPublicationSelector({ setGeoCity }) {
  const { inputValue, value, onChange, onInputChange } = useAsyncSelect()
  useEffect(() => setGeoCity(value), [setGeoCity, value])
  const { data, isLoading } = useGeoCity({ city: inputValue })
  let options = []
  if (data) {
    if (data.response) {
      options = data.response.results.map((g) => ({
        value: g.id,
        data: g,
        label: `${g.geoLocation.properties.city} (${g.geoLocation.properties.country})`
      }))
    }
  }
  return (
    <CustomSelect
      options={options}
      isLoading={!!inputValue && isLoading}
      onInputChange={onInputChange}
      value={value}
      onChange={onChange}
      placeholder="Type to search..."
      isClearable
    />
  )
}