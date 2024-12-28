import React from "react"
import cn from "classnames"
import { useRouter } from "next/router"
import Link from "next/link"

export function ErrorFallback({ error }) {
  return (
    <div>
      <article className="message is-danger">
        <div className="message-header">
          <p>Something went wrong</p>
        </div>
        <div className="message-body">{error.message}</div>
      </article>

      <button className="button" onClick={() => location.reload()}>
        Reload
      </button>
    </div>
  )
}

export function MenuInternalLinkItem({ href, label, isSub }) {
  const router = useRouter()
  const isActive = removeQuery(href) === removeQuery(router.asPath)
  return (
    <li>
      <MenuLink isSub={isSub} isActive={isActive} href={href}>
        {label}
      </MenuLink>
    </li>
  )
}

// `onClick`, `href`, and `ref` need to be passed to the DOM element
const MenuLink = React.forwardRef(function MenuLink(
  { onClick, href, isActive, children, isSub },
  ref
) {
  const className = isSub ? "Layout__side__sub" : "Layout__side__category"
  return (
    <Link href={href}>
      <a
        onClick={onClick}
        ref={ref}
        className={cn(
          { "is-active": isActive },
          "Layout__side__item",
          className
        )}
      >
        {children}
      </a>
    </Link>
  )
})

function removeQuery(href) {
  if (href.indexOf("?") > 0) return href.slice(0, href.indexOf("?"))
  else return href
}
