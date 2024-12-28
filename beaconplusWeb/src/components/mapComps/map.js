import L from "leaflet"
import { useEffect } from "react"

export const markerIcon = L.icon({
  iconSize: [25, 41],
  iconAnchor: [10, 41],
  popupAnchor: [2, -40],
  iconUrl: "/leaflet/marker-icon.png",
  shadowUrl: "/leaflet/marker-shadow.png"
})

export function getOSMTiles() {
  return L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  })
}

export function useMap(mapRef) {
  useEffect(() => {
    const tiles = getOSMTiles()
    const center = L.latLng(8.55, 47.37)
    const map = L.map("map", {
      center: center,
      zoom: 2,
      layers: [tiles]
    })

    mapRef.current = map
    return () => cleanup(map)
    // eslint-disable-next-line
  }, [])
}

//https://gis.stackexchange.com/questions/91355/leaflet-center-marker-and-popup-on-map-viewport
export function centerPopup(map, popup) {
  const px = map.project(popup._latlng) // find the pixel location on the map where the popup anchor is
  px.y -= popup._container.clientHeight / 2 // find the height of the popup container, divide by 2, subtract from the Y axis of marker location
  map.panTo(map.unproject(px), { animate: true }) // pan to new center
}

export const CustomMarker = L.Marker.extend({
  options: {
    icon: markerIcon
  }
})

export function cleanup(map) {
  if (map && map.remove) {
    map.off()
    map.remove()
  }
}

export function createCircle(latlng, radius) {
  return L.circle(latlng, {
    stroke: true,
    color: "#dd6633",
    weight: 1,
    fillColor: "#cc9966",
    fillOpacity: 0.4,
    radius: radius
  })
}

export function getLatlngFromGeoJSON(geoLocation) {
  return L.latLng(
    geoLocation.geometry.coordinates[1],
    geoLocation.geometry.coordinates[0]
  )
}
