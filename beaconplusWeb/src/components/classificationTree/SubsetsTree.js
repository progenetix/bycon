import { sampleSearchPageFiltersLink, subsetSearchPageFiltersLink } from "../../hooks/api"
import { subsetCountLabel } from "../helpersShared/labelHelpers"
import React, { useEffect, useMemo, useState } from "react"
import cn from "classnames"
import { FaAngleDown, FaAngleRight } from "react-icons/fa"
import Tippy from "@tippyjs/react"
import { FixedSizeTree as VTree } from "react-vtree"
import useDebounce from "../../hooks/debounce"
// import { min } from "lodash"
import { filterNode } from "./tree"

const ROW_HEIGHT = 28

export function SubsetsTree({
  tree,
  size,
  isFlat,
  datasetIds,
  checkedSubsets,
  checkboxClicked,
  sampleFilterScope
}) {
  const {
    searchInput,
    setSearchInput,
    filteredTree,
    debouncedSearchInput
  } = useFilterTree(tree)
  const [levelSelector, setLevelSelector] = useState(3)

  // console.log(filteredTree)

  const hasSelectedSubsets = checkedSubsets.length > 0
  const selectSamplesHref =
    hasSelectedSubsets &&
    sampleSelectUrl({ subsets: checkedSubsets, datasetIds })
  const selectSubsetsHref =
    hasSelectedSubsets &&
    subsetSelectUrl({ subsets: checkedSubsets, datasetIds })

  const height = Math.min(size * ROW_HEIGHT, 800)
  return (
    <>
      <div className="columns" style={{ padding: "0px" }}>
        <div className="column is-half">
          <input
            className="input mb-3"
            placeholder="Filter subsets e.g. by prefix ..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        {!isFlat && (
          <>
            <div className="column is-half">
            <div className="level-left">
              <div className="level-item">
                <p>Hierarchy Depth:</p>
              </div>
              <div className="level-item">
                <span className="select ">
                  <select
                    value={levelSelector}
                    onChange={(event) => {
                      setLevelSelector(event.target.value)
                    }}
                  >
                    <option value={0}>collapsed</option>
                    <option value={1}>1 level</option>
                    <option value={2}>2 levels</option>
                    <option value={3}>3 levels</option>
                    <option value={4}>4 levels</option>
                    <option value={5}>5 levels</option>
                    <option value={999}>all</option>
                  </select>
                </span>
              </div>
            </div>
            </div>
          </>
        )}
      </div>
      {hasSelectedSubsets && (
        <div className="columns" style={{ padding: "0px" }}>
          <div className="column is-half">
            <a className="button is-primary " href={selectSubsetsHref || null}>
              Compare Subsets from Selection
            </a>
          </div>
          {checkedSubsets.length === 1 && (
            <div className="column is-half">
              <a className="button is-primary " href={selectSamplesHref || null}>
                Search Samples from Selection
              </a>
            </div>
          )}
        </div>
      )}
      <div className="columns" style={{ padding: "10px" }}>
        <ul>
          {!hasSelectedSubsets && (
            <span className="tag is-dark">No Selection</span>
          )}
          {checkedSubsets.map((subset) => (
            <li className="tag is-primary" style={{ marginRight: "10px" }} key={subset.id}>
              {subset.label ? subset.label : subset.id} ({subset.count}){" "}
            </li>
          ))}
        </ul>
      </div>
      {filteredTree ? (
        <Tree
          levelSelector={levelSelector}
          height={height}
          datasetIds={datasetIds}
          checkboxClicked={checkboxClicked}
          sampleFilterScope={sampleFilterScope}
          isFlat={isFlat}
          search={debouncedSearchInput}
          tree={filteredTree}
        />
      ) : (
        <div className="notification">No results</div>
      )}
    </>
  )
}

function Tree({
  levelSelector,
  height,
  datasetIds,
  checkboxClicked,
  sampleFilterScope,
  isFlat,
  tree,
  search
}) {
  useEffect(() => {
    const state = Object.fromEntries(
      tree.children.map((rootNode) => [
        rootNode.uid,
        {
          open: search?.length > 0 || levelSelector > 0,
          subtreeCallback(node, ownerNode) {
            // Since subtreeWalker affects the ownerNode as well, we can check if the
            if (node !== ownerNode) {
              // nodes are the same, and run the action only if they aren't
              node.isOpen = search || node.data.nestingLevel < levelSelector
            }
          }
        }
      ])
    )
    treeRef.current.recomputeTree(state)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [levelSelector, tree])

  // eslint-disable-next-line react-hooks/exhaustive-deps
  // Memo needed for the checkbox state to work properly
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const treeWalker = useMemo(() => mkTreeWalker(tree), [search])
  const treeRef = React.createRef()

  return (
    <VTree
      ref={treeRef}
      treeWalker={treeWalker}
      height={height}
      itemSize={ROW_HEIGHT}
      itemData={{
        datasetIds,
        checkboxClicked,
        sampleFilterScope,
        isFlat
      }}
    >
      {Node}
    </VTree>
  )
}

// Node component receives all the data we created in the `treeWalker` +
// internal openness state (`isOpen`), function to change internal openness
// state (`toggle`) and `style` parameter that should be added to the root div.
function Node({
  data: { isLeaf, subsetId, subset, nestingLevel },
  treeData: {
    datasetIds,
    checkboxClicked,
    sampleFilterScope,
    isFlat
  },
  index,
  isOpen,
  style,
  setOpen
}) {
  const isSearchPossible = true // subset && canSearch(subset)
  const even = index % 2 === 0
  const detailsPage = "subset"
  return (
    <div
      style={{
        ...style,
        background: even ? "none" : "#fafafa"
      }}
      className="Subsets__tree__row"
    >
      <span
        className="Subsets__tree__cell"
        style={{ justifyContent: "center", width: 30, flex: "none" }}
      >
        {subset && isSearchPossible && (
          <input
            onChange={(e) =>
              checkboxClicked({ id: subset.id, checked: e.target.checked })
            }
            type="checkbox"
          />
        )}
      </span>
      <span
        className="Subsets__tree__cell"
        style={{
          flex: "1 1 auto"
        }}
      >
        <span
          className="Subsets__tree__info"
          style={{
            paddingLeft: `${nestingLevel * 20}px`
          }}
        >
          {!isFlat && (
            <span className={cn(isLeaf && "is-invisible")}>
              <Expander isOpen={isOpen} setOpen={setOpen} />
            </span>
          )}
          <Tippy content={`Show data for subset "${subset.label}"`}>
            <>
            {(subset?.label && (
              <span className="Subsets__tree__label" title={subset.label}>
              <a href={`/${detailsPage}/?id=${subsetId}&datasetIds=${datasetIds}`}>
              {subset.label}</a>: {subsetId}
              </span>
            ))
            || 
              <span className="Subsets__tree__label" title={subsetId}>
              <a href={`/${detailsPage}/?id=${subsetId}&datasetIds=${datasetIds}`}>
              {subsetId}</a>: {subsetId}
              </span>
            }
            </>
          </Tippy>
          {isSearchPossible ? (
            <Tippy content={`Click to retrieve samples for ${subsetId}`}>
              <a
                style={{ flexShrink: "0" }}
                href={sampleSelectUrl({
                  subsets: [subset],
                  datasetIds,
                  sampleFilterScope
                })}
              >
                <span>
                  &nbsp;{subsetCountLabel(subset)}
                </span>
              </a>
            </Tippy>
          ) : subset ? (
            <span>
              &nbsp;{subsetCountLabel(subset)}
            </span>
          ) : null}
        </span>
      </span>
    </div>
  )
}

function Expander({ isOpen, setOpen }) {
  return isOpen ? (
    <span onClick={() => setOpen(false)}>
      <span className="icon has-text-grey-dark is-clickable mr-2">
        <FaAngleDown size={18} />
      </span>
    </span>
  ) : (
    <span onClick={() => setOpen(true)}>
      <span className="icon has-text-grey-dark is-info is-clickable mr-2">
        <FaAngleRight size={18} />
      </span>
    </span>
  )
}

// This function prepares an object for yielding. We can yield an object
// that has `data` object with `id` and `isOpenByDefault` fields.
// We can also add any other data here.
const getNodeData = (node, nestingLevel) => {
  const subset = node.subset
  // Here we are sending the information about the node to the Tree component
  // and receive an information about the openness state from it. The
  // `refresh` parameter tells us if the full update of the tree is requested;
  // basing on it we decide to return the full node data or only the node
  // id to update the nodes order.

  const lineHeightPx = 16
  const labelLength = subset?.label?.length ?? 0

  // Useful for publications. 150 is approx. the number of chars before line break.
  // This is a quick fix and need to be adapted if the font style ever change.
  // This is a quick fix and it does not work in mobile.
  const defaultHeight =
    ROW_HEIGHT + Math.floor(labelLength / 150) * lineHeightPx

  return {
    data: {
      id: node.uid.toString(),
      defaultHeight,
      isLeaf: node.children.length === 0,
      isOpenByDefault: false,
      name: node.name,
      subsetId: node.id,
      subset,
      nestingLevel
    },
    nestingLevel,
    node
  }
}

const mkTreeWalker = (tree) => {
  return function* treeWalker() {
    // Here we send root nodes to the component.
    for (let i = 0; i < tree.children.length; i++) {
      yield getNodeData(tree.children[i], 0)
    }
    while (true) {
      // Get the parent component back. It will be the object
      // the `getNodeData` function constructed, so you can read any data from it.
      const parentMeta = yield

      for (let i = 0; i < parentMeta.node.children.length; i++) {
        yield getNodeData(
          parentMeta.node.children[i],
          parentMeta.nestingLevel + 1
        )
      }
    }
  }
}

const match = (debouncedSearchInput) => (node) => {
  const search = debouncedSearchInput.trim().toLowerCase()
  return (
    node.id.toLowerCase().includes(search) ||
    node.subset?.label?.toLowerCase().includes(search)
  )
}

function useFilterTree(tree) {
  const [searchInput, setSearchInput] = useState("")
  const debouncedSearchInput = useDebounce(searchInput, 500) || ""
  const filteredTree = filterNode(tree, match(debouncedSearchInput))
  return { searchInput, debouncedSearchInput, setSearchInput, filteredTree }
}

function sampleSelectUrl({ subsets, datasetIds }) {
  // here the `allTermsFilters` parameter has to be used instead of `filters` for
  // transfer to the search form since no `filters` field exist in the form
  // but rather several scoped fields
  const sampleFilterScope = "allTermsFilters"
  const filters = subsets.map(({ id }) => id).join(",")
  return sampleSearchPageFiltersLink({ datasetIds, sampleFilterScope, filters })
}

function subsetSelectUrl({ subsets, datasetIds }) {
  // here the `allTermsFilters` parameter has to be used instead of `filters` for
  // transfer to the search form since no `filters` field exist in the form
  // but rather several scoped fields
  const sampleFilterScope = "allTermsFilters"
  const filters = subsets.map(({ id }) => id).join(",")
  return subsetSearchPageFiltersLink({ datasetIds, sampleFilterScope, filters })
}

