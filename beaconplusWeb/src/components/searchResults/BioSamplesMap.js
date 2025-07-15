import React, { useRef } from "react"
// import ReactDOM from "react-dom"
import { createRoot } from 'react-dom';
import L from "leaflet"
import { centerPopup, createCircle, getLatlngFromGeoJSON, useMap } from "../mapComps/map"
import { groupBy } from "lodash"
import useDeepCompareEffect from "use-deep-compare-effect"
import PropTypes from "prop-types"
import { WithData } from "../Loader"
import Table from "../Table"

export default function BiosamplesMap({ apiReply, datasetId }) {
  return (
    <WithData
      apiReply={apiReply}
      render={(response) => (
        <Map biosamples={response.response.resultSets[0].results} height={640} datasetId={datasetId} />
      )}
    />
  )
}

BiosamplesMap.propTypes = {
  apiReply: PropTypes.object.isRequired,
  datasetId: PropTypes.string.isRequired
}

function Map({ biosamples, height, datasetId }) {
  const mapRef = useRef(null)
  useMap(mapRef)

  useDeepCompareEffect(() => {
    if (biosamples.length === 0) return
    const map = mapRef.current

    const byCoordinates = groupBy(
      biosamples,
      "geoLocation.geometry.coordinates"
    )

    const circles = Object.entries(byCoordinates).flatMap(([, biosamples]) => {
      const randomId = Math.random().toString(36).substring(2, 15)
      const geoLocation = biosamples[0]?.geoLocation
      if (!geoLocation) return []
      const radius = 3000 + 2000 * biosamples.length
      const root = document.getElementById('root');
      const reactRoot = createRoot(root);
      const render = () =>
        // eslint-disable-next-line react/no-render-return-value
          reactRoot.render(
          <BiosamplesTable biosamples={biosamples} datasetId={datasetId} />,
          document.getElementById(randomId)
        )
      const latlng = getLatlngFromGeoJSON(geoLocation)
      const circle = createCircle(latlng, radius).bindPopup(
        `
        <div class="mb-4">${geoLocation.properties.city} (${geoLocation.properties.country}): <b>${biosamples.length}</b> biosamples</div>
        <div id="${randomId}"></div>
        `,
        { minWidth: 400 }
      )
      circle.render = render
      return [circle]
    })

    map.on("popupopen", function (e) {
      const popup = e.target._popup
      centerPopup(map, popup)
      popup._source.render()
    })

    const layerGroup = L.featureGroup(circles).addTo(map)
    map.fitBounds(layerGroup.getBounds())
    return () => map.removeLayer(layerGroup)
  }, [biosamples, mapRef])

  return <div style={{ height, zIndex: 0 }} id="map" />
}

function BiosamplesTable({ biosamples, datasetId }) {
  const columns = React.useMemo(
    () => [
      {
        accessor: "id",
        Cell: function Cell(cellInfo) {
          return (
            <a
              href={`/biosample?id=${cellInfo.value}&datasetIds=${datasetId}`}
            >
              {cellInfo.value}
            </a>
          )
        }
      },
      {
        accessor: "description"
      }
    ],
    [datasetId]
  )

  return <Table columns={columns} data={biosamples} pageSize={10} />
}
