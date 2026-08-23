import { useMutation, useQueryClient } from '@tanstack/vue-query'

import { api } from '../api/client'
import { useSession } from './useSession'
import type { components } from '../domain/api'

type PaymentMethod = components['schemas']['PaymentMethod']

export type CheckoutInput = {
  customerName: string
  orderType: 'EAT_IN' | 'TAKEAWAY'
  paymentMethod: PaymentMethod
}

/** Checkout: convert the cart into a paid order in one atomic call. */
export function useCheckout() {
  const { sessionId } = useSession()
  const queryClient = useQueryClient()

  const checkoutMutation = useMutation({
    mutationFn: (input: CheckoutInput) =>
      api.checkout({
        session_id: sessionId.value,
        customer_name: input.customerName,
        order_type: input.orderType,
        payment_method: input.paymentMethod,
      }),
    onSuccess: (order) => {
      if (order.id != null) {
        queryClient.setQueryData(['order', order.id], order)
      }
      queryClient.removeQueries({ queryKey: ['cart', sessionId.value] })
    },
  })

  return { checkoutMutation }
}
