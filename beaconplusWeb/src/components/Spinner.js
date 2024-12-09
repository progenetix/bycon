import React from "react"

export function Spinner({ centered = true }) {
  const component = <span className="is-size-3 loader is-loading" />
  if (centered)
    return (
      <div className="level">
        <span className="level-item is-centered">{component}</span>
      </div>
    )
  return component
}
