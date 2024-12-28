import React from "react"
import "../styles/main.scss"
import { SWRConfig } from "swr"
import fetcher from "../hooks/fetcher"

export default function App({ Component, pageProps }) {
  return (
    // In this app we usually don't want auto refresh apiReply. It's a read-only/query type app and stale apiReply is acceptable.
    <SWRConfig value={{ fetcher, revalidateOnFocus: false }}>
      <Component {...pageProps} />
    </SWRConfig>
  )
}
