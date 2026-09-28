import { useEffect, useMemo, useState } from 'react'
import { fetchRestaurants } from './api'
import { MenuPanel } from './components/MenuPanel'
import { RestaurantList } from './components/RestaurantList'
import { RestaurantMap } from './components/RestaurantMap'
import type { Restaurant } from './types'
import { loadVisitedIds, saveVisitedIds } from './visited'

export default function App() {
  const [restaurantQuery, setRestaurantQuery] = useState('')
  const [mealQuery, setMealQuery] = useState('')
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [visitedIds, setVisitedIds] = useState<Set<number>>(() => loadVisitedIds())
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setLoading(true)
      fetchRestaurants(restaurantQuery, mealQuery)
        .then((data) => {
          setRestaurants(data)
          setError(null)
        })
        .catch((err: Error) => setError(err.message))
        .finally(() => setLoading(false))
    }, 200)

    return () => window.clearTimeout(handle)
  }, [restaurantQuery, mealQuery])

  const selected = useMemo(
    () => restaurants.find((r) => r.id === selectedId) ?? null,
    [restaurants, selectedId],
  )

  function selectRestaurant(restaurant: Restaurant) {
    setSelectedId(restaurant.id)
    setVisitedIds((current) => {
      const next = new Set(current)
      next.add(restaurant.id)
      saveVisitedIds(next)
      return next
    })
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="eyebrow">Zvolen</p>
          <h1>Denné menu</h1>
        </div>
        <form className="search" onSubmit={(e) => e.preventDefault()}>
          <label>
            Reštaurácia
            <input
              value={restaurantQuery}
              onChange={(e) => setRestaurantQuery(e.target.value)}
              placeholder="Názov alebo adresa"
            />
          </label>
          <label>
            Obed
            <input
              value={mealQuery}
              onChange={(e) => setMealQuery(e.target.value)}
              placeholder="Napr. rezeň, guláš, šalát"
            />
          </label>
        </form>
      </header>

      <section className="legend">
        <span><i className="dot dot--menu" /> Má denné menu</span>
        <span><i className="dot dot--empty" /> Bez denného menu</span>
        <span><i className="dot dot--visited" /> Už otvorené</span>
      </section>

      {error ? <p className="error">{error}</p> : null}

      <div className="layout">
        <div className="map-wrap">
          <RestaurantMap
            restaurants={restaurants}
            selectedId={selectedId}
            visitedIds={visitedIds}
            onSelect={selectRestaurant}
          />
          {selected ? <MenuPanel restaurant={selected} onClose={() => setSelectedId(null)} /> : null}
        </div>
        <section>
          <div className="list-head">
            <h2>Reštaurácie</h2>
            <p>{loading ? 'Načítavam…' : `${restaurants.length} výsledkov`}</p>
          </div>
          <RestaurantList
            restaurants={restaurants}
            selectedId={selectedId}
            visitedIds={visitedIds}
            onSelect={selectRestaurant}
          />
        </section>
      </div>
    </div>
  )
}
