import L from 'leaflet'
import { useEffect } from 'react'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import type { Restaurant } from '../types'
import { MenuItems } from './MenuItems'

const ZVOLEN: [number, number] = [48.5762, 19.1265]

function markerIcon(color: string) {
  return L.divIcon({
    className: 'map-pin',
    html: `<span class="map-pin__dot" style="background:${color}"></span>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -12],
  })
}

function pinColor(restaurant: Restaurant, visited: boolean) {
  if (visited) return '#8b9098'
  return restaurant.hasMenu ? '#1f7a45' : '#c45c26'
}

function FlyToSelected({ restaurant }: { restaurant: Restaurant | null }) {
  const map = useMap()

  useEffect(() => {
    if (!restaurant) return
    map.flyTo([restaurant.latitude, restaurant.longitude], 16, { duration: 0.6 })
  }, [map, restaurant])

  return null
}

type Props = {
  restaurants: Restaurant[]
  selectedId: number | null
  visitedIds: Set<number>
  onSelect: (restaurant: Restaurant) => void
}

export function RestaurantMap({ restaurants, selectedId, visitedIds, onSelect }: Props) {
  const selected = restaurants.find((r) => r.id === selectedId) ?? null

  return (
    <MapContainer center={ZVOLEN} zoom={14} className="map" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FlyToSelected restaurant={selected} />
      {restaurants.map((restaurant) => (
        <Marker
          key={restaurant.id}
          position={[restaurant.latitude, restaurant.longitude]}
          icon={markerIcon(pinColor(restaurant, visitedIds.has(restaurant.id)))}
          eventHandlers={{
            click: () => onSelect(restaurant),
          }}
        >
          <Popup>
            <div className="map-popup__details">
              <strong>{restaurant.name}</strong>
              <span>{restaurant.address}</span>
              <span>{restaurant.phone ?? 'Telefón nie je uvedený'}</span>
            </div>
            {restaurant.hasMenu ? (
              <ul className="menu map-popup__menu">
                <MenuItems items={restaurant.items} />
              </ul>
            ) : null}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
