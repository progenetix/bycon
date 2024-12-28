import PropTypes from "prop-types"
import { Infodot, Infolink } from "../Infodot"
import React from "react"

Label.propTypes = {
  label: PropTypes.node.isRequired,
  infoText: PropTypes.string,
  infoLink: PropTypes.string
}

export function Label({ label, infoText, infoLink }) {
  return (
    <div className="InputLabel__Wrapper">
      <label>{label}</label>
        {infoText && <Infodot infoText={infoText} />}
        {infoLink && <Infolink infoLink={infoLink} />}
    </div>
  )
}
