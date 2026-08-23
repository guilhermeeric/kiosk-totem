import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'

import { api } from '../api/client'

/** Payment attempt on an existing order (simulated on the backend). */
export function usePayment() {
  const queryClient = useQueryClient()

  const paymentMutation = useMutation({
    mutationFn: (input: { orderId: number; method: 'PIX' | 'CREDIT_CARD' | 'DEBIT_CARD' | 'CASH' }) =>
      api.createPayment(input.orderId, input.method),
    onSuccess: (payment) => {
      queryClient.invalidateQueries({ queryKey: ['order', payment.order_id] })
    },
  })

  return { paymentMutation }
}

/** Receipt: an order with its payment attempts. */
export function useOrder(orderId: number | null) {
  return useQuery({
    queryKey: ['order', orderId],
    queryFn: () => api.getOrder(orderId as number),
    enabled: () => orderId != null,
  })
}
