import React, { useState } from "react"
import cn from "classnames"
import { FaBars, FaTimes } from "react-icons/fa"
import { ErrorBoundary } from "react-error-boundary"
import { MarkdownParser } from "../components/MarkdownParser"
import Head from "next/head"
import {ErrorFallback, MenuInternalLinkItem} from "../components/MenuHelpers"
import Panel from "../components/Panel"
import { THISYEAR } from "../hooks/api"
import layoutConfig from "../site-specific/layout.yaml"

export function Layout({ title, headline, leadPanelMarkdown, tailPanelMarkdown, children }) {
  const [sideOpen, setSideOpen] = useState(false)
  return (
    <div className="Layout__app">
      <Head>
        <title>{title || ""}</title>
        <meta name="viewport" content="initial-scale=1.0, width=device-width" />
      </Head>
      <div className="Layout__header">
        {!sideOpen ? (
          <span
            className="Layout__burger icon"
            onClick={() => setSideOpen(true)}
          >
            <FaBars className="icon" />
          </span>
        ) : (
          <span
            className="Layout__burger icon"
            onClick={() => setSideOpen(false)}
          >
            <FaTimes className="icon" />
          </span>
        )}
      </div>
      <main className="Layout__main">
        <div className="Layout__side-background" />
        <div className="Layout__duo container">
          <aside className={cn("Layout__side", { open: sideOpen })}>
            <Side onClick={() => setSideOpen(false)} />
          </aside>
          <div className="Layout__lead">
            {headline && <h1 className="title is-4">{headline}</h1>}
            <ErrorBoundary
              FallbackComponent={ErrorFallback}
              onReset={() => {
                // reset the state of your app so the error doesn't happen again
              }}
            >
              {leadPanelMarkdown && (
                <Panel heading="" className="content">
                  {MarkdownParser(leadPanelMarkdown)}
                </Panel>
              )}
              {children}
              {tailPanelMarkdown && (
                <Panel heading="" className="content">
                  {MarkdownParser(tailPanelMarkdown)}
                </Panel>
              )}
            </ErrorBoundary>
          </div>
        </div>
      </main>
      <footer className="footer">
        <div className="content container has-text-centered">
          © {layoutConfig.sitePars.firstYear} - {THISYEAR} {layoutConfig.sitePars.longName} by
          the{" "}
          <a href={layoutConfig.sitePars.orgSiteLink}>{layoutConfig.sitePars.orgSiteLabel}</a>{" "}
          at the{" "}
          <a href="https://www.mls.uzh.ch/en/research/baudis/">
            University of Zurich
          </a>{" "}
          and the{" "}
          <a href="http://sib.swiss/baudis-michael/">
            Swiss Institute of Bioinformatics{" "}
            <span className="span-red">SIB</span>
          </a>{" "}
          is licensed under CC BY 4.0
          <a rel="license" href="https://creativecommons.org/licenses/by/4.0">
            <img className="Layout__cc__icons" src="/img/cc-cc.svg" />
            <img className="Layout__cc__icons" src="/img/cc-by.svg" />
          </a>
          <br />
          No responsibility is taken for the correctness of the data presented
          nor the results achieved with the Progenetix tools.
        </div>
      </footer>
    </div>
  )
}

function Side({ onClick }) {

  return (
    <div onClick={onClick}>
      <a href="/">
        <img
          className="Layout__side-logo"
          src={layoutConfig.sitePars.siteLogo}
          alt={layoutConfig.sitePars.siteLogoAlt}
        />
      </a>
      <ul className="Layout__side__items">
        {layoutConfig.layoutSideItems.map((item, i) => (
          <MenuInternalLinkItem
            key={i}
            href={item.href}
            label={item.label}
            isSub={item.isSub}
          />
        ))}
      </ul>
    </div>
  )
}
