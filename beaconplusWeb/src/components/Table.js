import {
  useAsyncDebounce,
  useGlobalFilter,
  usePagination,
  useTable,
  useSortBy
} from "react-table"
import React from "react"
import {
  FaAngleDoubleLeft,
  FaAngleDoubleRight,
  FaAngleLeft,
  FaAngleRight,
  FaAngleUp,
  FaAngleDown,
  FaInfoCircle
} from "react-icons/fa"
import { matchSorter } from "match-sorter"
import Tippy from "@tippyjs/react"

export default function Table({
  columns,
  data,
  pageSize = 10,
  hasGlobalFilter = false,
  hiddenColumns = [],
  sortBy = []
}) {
  const filterTypes = React.useMemo(
    () => ({
      fuzzyText: fuzzyTextFilterFn
    }),
    []
  )

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    prepareRow,
    page,
    canPreviousPage,
    canNextPage,
    pageOptions,
    pageCount,
    gotoPage,
    nextPage,
    previousPage,
    state,
    preGlobalFilteredRows,
    setGlobalFilter
  } = useTable(
    {
      columns,
      data,
      initialState: {
        pageIndex: 0,
        pageSize,
        hiddenColumns,
        sortBy
      },
      globalFilter: "fuzzyText",
      filterTypes
    },
    useGlobalFilter,
    useSortBy,
    usePagination
  )
  const { pageIndex } = state

  return (
    <>
      {hasGlobalFilter && (
        <GlobalFilter
          preGlobalFilteredRows={preGlobalFilteredRows}
          globalFilter={state.globalFilter}
          setGlobalFilter={setGlobalFilter}
        />
      )}{" "}
      {/* eslint-disable react/jsx-key */}
      <div className="table-container">
        <table
          className="table is-narrow is-hoverable is-fullwidth"
          {...getTableProps()}
        >
          <Header headerGroups={headerGroups} />
          <Body
            getTableBodyProps={getTableBodyProps}
            page={page}
            prepareRow={prepareRow}
          />
        </table>
      </div>
      {/* eslint-enable react/jsx-key */}
      {pageCount > 1 && (
        <Pagination
          gotoPage={gotoPage}
          canPreviousPage={canPreviousPage}
          previousPage={previousPage}
          nextPage={nextPage}
          canNextPage={canNextPage}
          pageCount={pageCount}
          pageIndex={pageIndex}
          pageOptions={pageOptions}
        />
      )}{" "}
    </>
  )
}

function GlobalFilter({
  preGlobalFilteredRows,
  globalFilter,
  setGlobalFilter
}) {
  const count = preGlobalFilteredRows.length
  const [value, setValue] = React.useState(globalFilter)
  const onChange = useAsyncDebounce((value) => {
    setGlobalFilter(value || undefined)
  }, 200)

  return (
    <div className="mb-3">
      <b>Search: </b>{" "}
      <input
        value={value || ""}
        onChange={(e) => {
          setValue(e.target.value)
          onChange(e.target.value)
        }}
        placeholder={`${count} records...`}
        style={{
          border: "0"
        }}
      />
    </div>
  )
}

function Body({ getTableBodyProps, page, prepareRow }) {
  return (
    <tbody {...getTableBodyProps()}>
      {page.map((row, ri) => {
        prepareRow(row)
        return (
          <tr key={ri} {...row.getRowProps()}>
            {row.cells.map((cell, ci) => {
              return (
                <td
                  key={ci}
                  {...cell.getCellProps()}
                  style={{ position: "relative" }}
                >
                  {cell.render("Cell")}
                </td>
              )
            })}
          </tr>
        )
      })}
    </tbody>
  )
}

function Header({ headerGroups }) {
  return (
    <thead>
      {headerGroups.map((column, hi) => (
        <tr key={hi} {...column.getHeaderGroupProps()}>
          {column.headers.map((column, ci) => (
            <th
              key={ci}
              {...column.getHeaderProps(column.getSortByToggleProps())}
            >
              <span className="is-flex">
                {column.render("Header")}
                {column.isSorted && (
                  <span>
                    {column.isSortedDesc ? (
                      <span className="icon">
                        <FaAngleDown />
                      </span>
                    ) : (
                      <span className="icon">
                        <FaAngleUp />
                      </span>
                    )}
                  </span>
                )}
              </span>
            </th>
          ))}
        </tr>
      ))}
    </thead>
  )
}

function Pagination({
  gotoPage,
  canPreviousPage,
  previousPage,
  nextPage,
  canNextPage,
  pageCount,
  pageIndex,
  pageOptions
}) {
  return (
    <div className="DataTable__pagination">
      <span>
        <button
          className="button is-small"
          onClick={() => gotoPage(0)}
          disabled={!canPreviousPage}
        >
          <FaAngleDoubleLeft className="icon is-small" />
        </button>{" "}
        <button
          className="button is-small"
          onClick={() => previousPage()}
          disabled={!canPreviousPage}
        >
          <FaAngleLeft className="icon is-small" />
        </button>{" "}
        <button
          className="button is-small"
          onClick={() => nextPage()}
          disabled={!canNextPage}
        >
          <FaAngleRight className="icon is-small" />
        </button>{" "}
        <button
          className="button is-small"
          onClick={() => gotoPage(pageCount - 1)}
          disabled={!canNextPage}
        >
          <FaAngleDoubleRight className="icon is-small" />
        </button>{" "}
      </span>
      <span>
        Page{" "}
        <strong>
          {pageIndex + 1} of {pageOptions.length}
        </strong>
      </span>
    </div>
  )
}

function fuzzyTextFilterFn(rows, id, filterValue) {
  let keys
  if (Array.isArray(id)) {
    keys = id.map((id) => (row) => row.values[id])
  } else keys = [(row) => row.values[id]]
  return matchSorter(rows, filterValue, {
    keys
  })
}

// Let the table remove the filter if the string is empty
fuzzyTextFilterFn.autoRemove = (val) => !val

export function TooltipHeader(short, full) {
  return (
    <Tippy theme="light-border" content={full}>
      <abbr className="abbr">{short}</abbr>
    </Tippy>
  )
}

export function InfodotHeader(short, full) {
  return (
    <span>
      {short}
      <Tippy theme="light-border" content={full}>
        <span className="icon__wrapper">
          <FaInfoCircle className="ml-2 icon is-small has-text-grey-light" />
        </span>
      </Tippy>
    </span>
  )
}
