import React from "react"

export function Admonition({ title, content }) {
  return (
<div className="admonition">
  <div className="admonition-title">{title}</div>
  <div dangerouslySetInnerHTML={{ __html: content }}></div>
</div>
  )
}
