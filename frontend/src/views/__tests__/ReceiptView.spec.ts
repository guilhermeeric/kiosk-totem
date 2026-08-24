import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'

import ReceiptView from '../ReceiptView.vue'

const { useOrder } = vi.hoisted(() => ({ useOrder: vi.fn() }))

const orderRef = ref<{
  id: number
  customer_name: string
  order_type: string
  total: string
  items: { item_id: number; quantity: number; total: string }[]
  payments: { id: number | null; method: string; status: string }[]
} | null>(null)
const isPending = ref(false)
const errorRef = ref<unknown>(null)

const cartData = ref<{ id: number; handed_off_at?: string | null }>({ id: 7, handed_off_at: null })

vi.mock('../../composables/usePayment', () => ({ useOrder }))
vi.mock('../../composables/useCart', () => ({
  useCart: () => ({ cartQuery: { data: cartData } }),
}))
vi.mock('../../composables/useSession', () => ({
  useSession: () => ({ sessionId: ref('sess-1'), clearSession: vi.fn() }),
}))
vi.mock('../../composables/useItems', () => ({
  useItems: () => ({ name: () => 'Classic Burger', byId: ref(new Map()) }),
}))
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

function mountView() {
  return mount(ReceiptView, { props: { id: '42' } })
}

beforeEach(() => {
  orderRef.value = {
    id: 42,
    customer_name: 'Ana',
    order_type: 'EAT_IN',
    total: '10.00',
    items: [{ item_id: 7, quantity: 1, total: '10.00' }],
    payments: [{ id: 1, method: 'PIX', status: 'PAID' }],
  }
  isPending.value = false
  errorRef.value = null
  cartData.value = { id: 7, handed_off_at: null }
  useOrder.mockClear()
  useOrder.mockReturnValue({ data: orderRef, isPending, error: errorRef })
})

describe('ReceiptView tracking affordances', () => {
  it('renders the order number and payment status', () => {
    const wrapper = mountView()
    expect(wrapper.text()).toContain('42')
    expect(wrapper.text()).toContain('PIX')
  })

  it('shows a tracking QR pointing at /track/42 on every receipt', () => {
    const wrapper = mountView()
    const img = wrapper.find('img[alt="Order tracking QR"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toContain('/qr?content=')
    expect(img.attributes('src')).toContain('%2Ftrack%2F42')
  })

  it('offers a direct track button when the order was placed on a phone (handed off)', () => {
    cartData.value = { id: 7, handed_off_at: '2026-01-01T00:00:00' }
    const wrapper = mountView()
    const link = wrapper.find('a[href="/track/42"]')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('Track your order')
  })

  it('hides the track button on the kiosk (not handed off) — QR only', () => {
    const wrapper = mountView()
    expect(wrapper.find('a[href="/track/42"]').exists()).toBe(false)
  })
})
