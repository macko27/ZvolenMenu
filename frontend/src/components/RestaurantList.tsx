import type { Restaurant } from '../types'
import { MenuItems } from './MenuItems'

type Props = {
  restaurants: Restaurant[]
  selectedId: number | null
  visitedIds: Set<number>
  onSelect: (restaurant: Restaurant) => void
}

export function RestaurantList({ restaurants, selectedId, visitedIds, onSelect }: Props) {
  if (restaurants.length === 0) {
    return <p className="empty">Žiadna reštaurácia nevyhovuje hľadaniu.</p>
  }

  return (
    <div className="list">
      {restaurants.map((restaurant) => {
        const visited = visitedIds.has(restaurant.id)
        const status = visited
          ? 'Navštívené'
          : restaurant.hasMenu
            ? 'Denné menu'
            : 'Bez denného menu'

        return (
          <article
            key={restaurant.id}
            className={`card ${selectedId === restaurant.id ? 'card--selected' : ''} ${visited ? 'card--visited' : ''}`}
          >
            <button type="button" className="card__header" onClick={() => onSelect(restaurant)}>
              <div>
                <h2>{restaurant.name}</h2>
                <p>{restaurant.address}</p>
              </div>
              <span
                className={`badge ${visited ? 'badge--visited' : restaurant.hasMenu ? 'badge--menu' : 'badge--empty'}`}
              >
                {status}
              </span>
            </button>

            {restaurant.hasMenu ? (
              <ul className="menu">
                <MenuItems items={restaurant.items} />
              </ul>
            ) : (
              <p className="menu-missing">Dnes nie je zverejnené denné menu.</p>
            )}
          </article>
        )
      })}
    </div>
  )
}
