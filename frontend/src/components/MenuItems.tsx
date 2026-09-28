import type { MenuItem } from '../types'

function formatPrice(price: number) {
  return price.toFixed(2).replace('.', ',') + ' €'
}

type Props = {
  items: MenuItem[]
}

export function MenuItems({ items }: Props) {
  const categories = items.reduce<Map<string, MenuItem[]>>((groups, item) => {
    const categoryItems = groups.get(item.category) ?? []
    categoryItems.push(item)
    groups.set(item.category, categoryItems)
    return groups
  }, new Map())

  return (
    <>
      {Array.from(categories, ([category, categoryItems]) => (
        <li key={category} className="menu__group">
          <span className="menu__category">{category}</span>
          <ul className="menu menu__items">
            {categoryItems.map((item) => (
              <li key={item.id}>
                <div>
                  <strong>{item.name}</strong>
                  {item.description ? <small>{item.description}</small> : null}
                </div>
                <span className="menu__price">{formatPrice(item.price)}</span>
              </li>
            ))}
          </ul>
        </li>
      ))}
    </>
  )
}
