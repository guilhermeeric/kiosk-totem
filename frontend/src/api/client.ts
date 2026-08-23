import type { components } from '../domain/api'

type CartResponse = components['schemas']['CartResponse']
type ItemResponse = components['schemas']['ItemResponse']
type OrderResponse = components['schemas']['OrderResponse']
type OrderType = components['schemas']['OrderType']
type PaymentMethod = components['schemas']['PaymentMethod']
type PaymentResponse = components['schemas']['PaymentResponse']

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail: unknown = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // non-JSON error body; keep statusText
    }
    const message = typeof detail === 'string' ? detail : `Request failed (${res.status})`
    throw new ApiError(res.status, message)
  }
  return res.json() as Promise<T>
}

/**
 * Typed API client — the frontend seam over the OpenAPI contract.
 * Every call returns the authoritative domain shape from the backend.
 */
export const api = {
  listItems: () => request<ItemResponse[]>('/items'),

  createCart: (sessionId: string) =>
    request<CartResponse>('/carts', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),

  getCart: (sessionId: string) => request<CartResponse>(`/carts/${encodeURIComponent(sessionId)}`),

  addCartItem: (sessionId: string, itemId: number, quantity: number) =>
    request<CartResponse>(`/carts/${encodeURIComponent(sessionId)}/items`, {
      method: 'PUT',
      body: JSON.stringify({ item_id: itemId, quantity }),
    }),

  removeCartItem: (sessionId: string, itemId: number) =>
    request<CartResponse>(`/carts/${encodeURIComponent(sessionId)}/items/${itemId}`, {
      method: 'DELETE',
    }),

  updateCartItem: (sessionId: string, itemId: number, quantity: number) =>
    request<CartResponse>(`/carts/${encodeURIComponent(sessionId)}/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity }),
    }),

  checkout: (input: {
    session_id: string
    customer_name: string
    order_type: OrderType
    payment_method: PaymentMethod
  }) =>
    request<OrderResponse>('/orders', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  createPayment: (orderId: number, method: PaymentMethod) =>
    request<PaymentResponse>(`/orders/${orderId}/payments`, {
      method: 'POST',
      body: JSON.stringify({ method }),
    }),

  getOrder: (orderId: number) => request<OrderResponse>(`/orders/${orderId}`),
}
