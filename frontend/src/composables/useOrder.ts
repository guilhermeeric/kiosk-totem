import { useQuery } from '@tanstack/vue-query'

import { api } from '../api/client'

/** Fetch an order with its payment attempts. Polls when given an interval. */
export function useOrder(orderId: number | null, refetchIntervalMs?: number) {
  return useQuery({
    queryKey: ['order', orderId],
    queryFn: () => api.getOrder(orderId as number),
    enabled: () => orderId != null,
    refetchInterval: refetchIntervalMs ?? false,
  })
}
