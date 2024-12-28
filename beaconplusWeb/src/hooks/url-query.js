import React, { useCallback, useEffect, useState } from "react"
import { useRouter } from "next/router"

/**
 * https://github.com/vercel/next.js/issues/8259
 * This work around returns a define query only if the component has been mounted.
 * This is necessary when using custom export and no SSR.
 */
export function useReadyRouter() {
  const router = useRouter()
  const [ready, setReady] = useState(false)
  useEffect(() => {
    if (testRouterReady(router) && !ready) {
      setReady(true)
    }
  }, [ready, router])

  return ready ? router : undefined
}

export function useUrlQuery() {
  const router = useReadyRouter()

  function getUrlQuery() {
    return (
      router && {
        ...router.query,
        ...Object.fromEntries(
          new URLSearchParams(window.location.search).entries()
        )
      }
    )
  }

  const setUrlQuery = useCallback(
    (values, options = { replace: false, keepExisting: false }) => {
      if (!router) return
      const init = options.keepExisting ? window.location.search : ""
      const params = new URLSearchParams(init)
      Object.entries(values).forEach(([k, v]) => params.set(k, v))
      const url = `${location.pathname}?${params}`
      options.replace ? router.replace(url) : router.push(url)
    },
    [router]
  )
  return router ? { urlQuery: getUrlQuery(), setUrlQuery } : undefined
}

const isDynamicPage = (router) => /\[.+\]/.test(router.route)
const testRouterReady = (router) =>
  !isDynamicPage(router) || router.asPath !== router.route

export const withUrlQuery = (WrappedComponent) => {
  const QueryProvider = (props) => {
    const query = useUrlQuery()
    if (!query) return null //only renders when component
    return (
      <WrappedComponent
        urlQuery={query.urlQuery}
        setUrlQuery={query.setUrlQuery}
        {...props}
      />
    )
  }
  return QueryProvider
}
