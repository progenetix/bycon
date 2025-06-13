import React, { useRef } from "react"
import L from "leaflet"
import {
  centerPopup,
  createCircle,
  getLatlngFromGeoJSON,
  useMap
} from "../mapComps/map"
import { PublicationCompactTable } from "./PublicationTables"
import { groupBy } from "lodash"
import useDeepCompareEffect from "use-deep-compare-effect"
// import ReactDOM from "react-dom"
import { createRoot } from 'react-dom';

export default function PublicationsMap({ publications, height }) {
  const mapRef = useRef(null)
  useMap(mapRef)

  useDeepCompareEffect(() => {
    if (publications.length === 0) return
    const map = mapRef.current

    const byCoordinates = groupBy(
      publications,
      "geoLocation.geometry.coordinates"
    )

    const circles = Object.entries(byCoordinates).map(([, publications]) => {
      const randomId = Math.random().toString(36).substring(2, 15)
      const geoLocation = publications[0].geoLocation
      const radius = 3000 + 2000 * publications.length
      const root = document.getElementById('root');
      const reactRoot = createRoot(root);
      const render = () =>
        // eslint-disable-next-line react/no-render-return-value
          reactRoot.render(
          <PublicationCompactTable publications={publications} />,
          document.getElementById(randomId)
        )
      const latlng = getLatlngFromGeoJSON(geoLocation)
      const circle = createCircle(latlng, radius).bindPopup(
        `
        <div>${geoLocation.properties.city} (${geoLocation.properties.country}): <b>${publications.length}</b> publications</div>
        <div id="${randomId}"></div>
        `,
        { minWidth: 400, keepInView: true }
      )
      circle.render = render
      return circle
    })

    map.on("popupopen", function (e) {
      const popup = e.target._popup
      centerPopup(map, popup)
      popup._source.render()
    })

    const layerGroup = L.featureGroup(circles).addTo(map)
    map.fitBounds(layerGroup.getBounds())
    return () => map.removeLayer(layerGroup)
  }, [publications, mapRef])

  return <div style={{ height, zIndex: 0 }} id="map" />
}
