import { useAsyncSelect } from "../../hooks/asyncSelect"
import { useCytomapper } from "../../hooks/api"
import { useGeneSpanSelect } from "../formShared/GenespanUtilities.js"
import CustomSelect from "../Select"
import React, { useState } from "react"
import PropTypes from "prop-types"
import cn from "classnames"
import { FaCogs } from "react-icons/fa"
import { WithData } from "../Loader"
import { Infodot } from "../Infodot"

FormUtilitiesButtons.propTypes = {
  onGeneSpansClick: PropTypes.func.isRequired,
  geneSpansPanelOpen: PropTypes.bool.isRequired,
  onCytoBandClick: PropTypes.func.isRequired,
  cytoBandPanelOpen: PropTypes.bool.isRequired
}

export function useFormUtilities() {
  const [cytoBandPanelOpen, setCytoBandPanelOpen] = useState(false)
  const [geneSpansPanelOpen, setgeneSpansPanelOpen] = useState(false)
  const onCytoBandClick = () => {
    setCytoBandPanelOpen(!cytoBandPanelOpen)
    setgeneSpansPanelOpen(false)
  }
  const onCytoBandCloseClick = () => setCytoBandPanelOpen(false)

  const onGeneSpansClick = () => {
    setgeneSpansPanelOpen(!geneSpansPanelOpen)
    setCytoBandPanelOpen(false)
  }
  const onGeneSpansCloseClick = () => setgeneSpansPanelOpen(false)
  return {
    cytoBandPanelOpen,
    onCytoBandClick,
    onCytoBandCloseClick,
    geneSpansPanelOpen,
    onGeneSpansClick,
    onGeneSpansCloseClick
  }
}

export function FormUtilitiesButtons({
  onGeneSpansClick,
  geneSpansPanelOpen,
  onCytoBandClick,
  cytoBandPanelOpen
}) {
  return (
    <div>
      <button
        className={cn("button", [geneSpansPanelOpen && "is-link"])}
        style={{ marginLeft: "8px" }}
        onClick={onGeneSpansClick}
      >
        <span className="icon">
          <FaCogs />
        </span>
        <span>Gene Spans</span>
      </button>
      <button
        className={cn("button", [cytoBandPanelOpen && "is-link"])}
        onClick={onCytoBandClick}
      >
        <span className="icon">
          <FaCogs />
        </span>
        <span>Cytoband(s)</span>
      </button>
    </div>
  )
}

export function GeneSpansUtility({ onClose, setFormValue }) {
  const { inputValue, value, onChange, onInputChange } = useAsyncSelect()
  const { options, error, isLoading } = useGeneSpanSelect(inputValue)
  const onApply = (optionValue) => {
    setFormValue("start", optionValue.start)
    setFormValue("end", optionValue.end)
    setFormValue("referenceName", "refseq:"+optionValue.accessionVersion)
    onClose()
  }
  const renderValue = (optionValue) => (
    <div className="content">
      <div>
        Start: <b>{optionValue.start}</b>
      </div>
      <div>
        End: <b>{optionValue.end}</b>
      </div>
      <div>
        Chromosome: <b>{optionValue.referenceName}</b>
      </div>
      <div>
        Sequence Accession: <b>refseq:{optionValue.accessionVersion}</b>
      </div>
      <div>
        Please use the <b>Apply</b> button to copy the values to the{" "}
        <i>referenceName</i>, <i>start</i> and <i>end</i> fields. For use in 
        Fusion queries (<i>mateName</i> etc.) you have to insert the values
        manually.
      </div>
    </div>
  )
  return (
    <div className="message is-link mb-6">
      <div className="message-body">
        <p className="subtitle is-5">
          Gene Spans{" "}
          <Infodot
            infoText={
              "Type a gene symbol and select to transfer coordinates into Reference Name (chromosome), Start and End fields, e.g. for a Range Query or further adjustment."
            }
          />
        </p>
        <CustomSelect
          className="mb-3"
          options={options}
          isLoading={!!inputValue && isLoading}
          onInputChange={onInputChange}
          value={value}
          onChange={onChange}
          placeholder="Type to search..."
        />

        {error && <Error />}
        {value && (
          <>
            <div className="content has-text-black">
              {renderValue(value.value)}
            </div>
            <div className="buttons">
              <button
                onClick={() => onApply(value.value)}
                className="button is-primary"
              >
                Apply
              </button>
              <button onClick={onClose} className="button  is-outlined">
                Close
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

GeneSpansUtility.propTypes = {
  onClose: PropTypes.func.isRequired,
  setFormValue: PropTypes.func.isRequired
}

export function CytoBandsUtility({ onClose, setFormValue }) {
  const [inputValue, setInputValue] = useState("")
  const [searchValue, setSearchValue] = useState("")
  const apiReply = useCytomapper(searchValue)
  const onApply = (data) => {
    setFormValue("start", data.response.results[0].genomic_location.interval.start.value)
    setFormValue("end", data.response.results[0].genomic_location.interval.end.value)
    setFormValue("referenceName", data.response.results[0].genomic_location.sequence_id)
    onClose()
  }
  const onSubmit = (e) => {
    e.preventDefault()
    setSearchValue(inputValue)
  }
  return (
    <div>
      <div className="message is-link mb-6">
        <div className="message-body">
          <p className="subtitle is-5">
            CytoBands
            <Infodot
              infoText={
                "Type a cytoband or range and select to transfer coordinates into Reference Name (chromosome), Start and End fields, e.g. for a Range Query or further adjustment."
              }
            />
          </p>
          <form onSubmit={onSubmit} className="field has-addons mb-4">
            <div className="control">
              <input
                onChange={(e) => setInputValue(e.target.value)}
                className="input"
                type="text"
                placeholder="Ex: 8q21"
              />
            </div>
            <div className="control">
              <button className="button" type="submit">
                Search
              </button>
            </div>
          </form>
          {searchValue && (
            <WithData
              apiReply={apiReply}
              render={(data) => {
                const info = data.response.results[0]?.info
                const hasResults = !!info?.cytoBands
                return (
                  <>
                    {hasResults ? (
                      <CytoBandsData data={data.response.results} />
                    ) : (
                      <div className="notification is-light">No results.</div>
                    )}
                    <div className="buttons">
                      <button
                        disabled={!hasResults}
                        onClick={() => onApply(data)}
                        className="button is-primary"
                      >
                        Apply
                      </button>
                      <button onClick={onClose} className="button is-outlined">
                        Close
                      </button>
                    </div>
                  </>
                )
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}

function CytoBandsData({ data }) {
  return (
    <div className="content has-text-black">
      <div>
        CytoBands: <b>{data[0].chromosome_location.chr}{data[0].info.cytoBands}</b>
      </div>
      <div>
        Chromosome: <b>{data[0].chromosome_location.chr}</b>
      </div>
      <div>
        Sequence ID: <b>{data[0].genomic_location.sequence_id}</b>
      </div>
      <div>
        Start: <b>{data[0].genomic_location.interval.start.value}</b>
      </div>
      <div>
        End: <b>{data[0].genomic_location.interval.end.value}</b>
      </div>
      <div>
        Please use the <b>Apply</b> button to copy the values to the{" "}
        <i>referenceName</i>, <i>start</i> and <i>end</i> fields. For use in 
        Fusion queries (<i>mateName</i> etc.) you have to insert the values
        manually.
      </div>
    </div>
  )
}

CytoBandsUtility.propTypes = {
  onClose: PropTypes.func.isRequired,
  setFormValue: PropTypes.func.isRequired
}

function Error() {
  return <div className="notification is-warning">Could not load data...</div>
}
