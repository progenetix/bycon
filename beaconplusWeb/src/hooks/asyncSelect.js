import { useState } from "react"
import { debounce } from "lodash"

// Use with react-select
export function useAsyncSelect() {
  const [inputValue, setInputValue] = useState(null)
  const [value, setValue] = useState(null)
  const onInputChange = debounce((v, { action }) => {
    if (action === "input-change") {
      setInputValue(v)
      setValue(null)
    }
  }, 200)
  const onChange = (v, { action }) => {
    switch (action) {
      case "remove-value":
      case "pop-value":
      case "select-option":
        setValue(v)
        break
      case "clear":
        setValue(null)
        break
    }
  }
  return { inputValue, onInputChange, value, onChange }
}
