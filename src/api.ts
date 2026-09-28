import type { Restaurant } from './types'

function todayIsoDate() {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  return new Date(now.getTime() - offset * 60_000).toISOString().slice(0, 10)
}

export async function fetchRestaurants(restaurant: string, meal: string): Promise<Restaurant[]> {
  const params = new URLSearchParams({ date: todayIsoDate() })
  if (restaurant.trim()) params.set('restaurant', restaurant.trim())
  if (meal.trim()) params.set('meal', meal.trim())

  const response = await fetch(`/api/restaurants?${params.toString()}`)
  if (!response.ok) {
    throw new Error('Nepodarilo sa načítať reštaurácie.')
  }
  return response.json()
}

export { todayIsoDate }
