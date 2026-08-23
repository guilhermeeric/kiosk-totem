import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { api } from '../api/client'
import type { components } from '../domain/api'

type Item = components['schemas']['ItemResponse']

/** Menu items: shared query + id → name lookup for cart/order line items. */
export function useItems() {
  const itemsQuery = useQuery({
    queryKey: ['items'],
    queryFn: api.listItems,
  })

  const byId = computed(() => {
    const map = new Map<number, Item>()
    for (const item of itemsQuery.data.value ?? []) {
      map.set(item.id, item)
    }
    return map
  })

  const name = (itemId: number) => byId.value.get(itemId)?.name ?? `Item #${itemId}`

  return { itemsQuery, byId, name }
}
