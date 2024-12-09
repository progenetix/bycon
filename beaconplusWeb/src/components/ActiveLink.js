import React from "react"
import cn from "classnames"
import { useRouter } from "next/router"
import Link from "next/link"

export default function ActiveLink({ href, label }) {
  const router = useRouter()
  const isActive = router.asPath === href
  return (
    <Link href={href}>
      <a className={cn("navbar-item", { "Nav__Link--active": isActive })}>
        {label}
      </a>
    </Link>
  )
}
