import { todayIsoDate } from './api'

const storageKey = () => `zvolen-menu-visited-${todayIsoDate()}`

export function loadVisitedIds(): Set<number> {
  try {
    const raw = localStorage.getItem(storageKey())
    if (!raw) return new Set()
    const parsed = JSON.parse(raw) as number[]
    return new Set(parsed)
  } catch {
    return new Set()
  }
}

export function saveVisitedIds(ids: Set<number>) {
  localStorage.setItem(storageKey(), JSON.stringify([...ids]))
}
