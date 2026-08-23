import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import { api } from '../api/client'
import { useSession } from './useSession'

/** Cart server state: the API returns the authoritative cart on every call. */
export function useCart() {
  const { sessionId } = useSession()
  const queryClient = useQueryClient()

  const cartQuery = useQuery({
    queryKey: ['cart', sessionId],
    queryFn: () => api.getCart(sessionId.value),
    enabled: () => Boolean(sessionId.value),
  })

  const addItem = useMutation({
    mutationFn: (input: { itemId: number; quantity: number }) =>
      api.addCartItem(sessionId.value, input.itemId, input.quantity),
    onSuccess: (cart) => queryClient.setQueryData(['cart', sessionId.value], cart),
  })

  const removeItem = useMutation({
    mutationFn: (itemId: number) => api.removeCartItem(sessionId.value, itemId),
    onSuccess: (cart) => queryClient.setQueryData(['cart', sessionId.value], cart),
  })

  const updateQuantity = useMutation({
    mutationFn: (input: { itemId: number; quantity: number }) =>
      api.updateCartItem(sessionId.value, input.itemId, input.quantity),
    onSuccess: (cart) => queryClient.setQueryData(['cart', sessionId.value], cart),
  })

  return { cartQuery, addItem, removeItem, updateQuantity }
}
