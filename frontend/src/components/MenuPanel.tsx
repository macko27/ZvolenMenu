import type { Restaurant } from '../types'
import { MenuItems } from './MenuItems'

type Props = {
  restaurant: Restaurant
  onClose: () => void
}

export function MenuPanel({ restaurant, onClose }: Props) {
  return (
    <aside className="panel">
      <div className="panel__top">
        <div>
          <h2>{restaurant.name}</h2>
          <p>{restaurant.address}</p>
          {restaurant.phone ? <p>{restaurant.phone}</p> : null}
        </div>
        <button type="button" className="panel__close" onClick={onClose} aria-label="Zavrieť">
          ×
        </button>
      </div>
      {restaurant.note ? <p className="panel__note">{restaurant.note}</p> : null}
      {restaurant.hasMenu ? (
        <ul className="menu">
          <MenuItems items={restaurant.items} />
        </ul>
      ) : (
        <p className="menu-missing">Táto reštaurácia dnes nemá denné menu.</p>
      )}
    </aside>
  )
}
