export type MenuItem = {
  id: number
  category: string
  name: string
  description: string | null
  price: number
}

export type Restaurant = {
  id: number
  name: string
  address: string
  latitude: number
  longitude: number
  phone: string | null
  website: string | null
  hasMenu: boolean
  note: string | null
  items: MenuItem[]
}
