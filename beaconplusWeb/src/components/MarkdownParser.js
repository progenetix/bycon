import unified from "unified"
import parse from "remark-parse"
import remark2react from "remark-react"

export function MarkdownParser(md) {
  return unified().use(parse).use(remark2react).processSync(md).result
}
