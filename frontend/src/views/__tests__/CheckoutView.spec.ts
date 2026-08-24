import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { computed, ref } from 'vue'

import { ApiError } from '../../api/client'
import CheckoutView from '../CheckoutView.vue'

const checkoutMutate = vi.fn()
const push = vi.fn()
const cartData = ref<{
  items: { item_id: number; quantity: number; unit_price: string; total: string }[]
  total: string
}>({
  items: [{ item_id: 1, quantity: 1, unit_price: '10.00', total: '10.00' }],
  total: '10.00',
})
const itemStock = ref(new Map<number, { stock: number }>([[1, { stock: 10 }]]))

vi.mock('../../composables/useSession', () => ({
  useSession: () => ({ sessionId: ref('sess-1') }),
}))

vi.mock('../../composables/useCart', () => ({
  useCart: () => ({
    cartQuery: { data: cartData, isPending: ref(false) },
  }),
}))

vi.mock('../../composables/useItems', () => ({
  useItems: () => ({
    name: (itemId: number) => (itemId === 1 ? 'Coffee' : `Item #${itemId}`),
    byId: computed(() => itemStock.value),
  }),
}))

vi.mock('../../composables/useCheckout', () => ({
  useCheckout: () => ({
    checkoutMutation: { isPending: ref(false), mutate: checkoutMutate },
  }),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

function mountView() {
  return mount(CheckoutView)
}

function payButton(wrapper: ReturnType<typeof mountView>) {
  const btn = wrapper.findAll('button').find((b) => b.text().startsWith('Pay'))
  if (!btn) throw new Error('Pay button not found')
  return btn
}

function terminalButton(wrapper: ReturnType<typeof mountView>, label: string) {
  const btn = wrapper.findAll('button').find((b) => b.text().includes(label))
  if (!btn) throw new Error(`Terminal button ${label} not found`)
  return btn
}

beforeEach(() => {
  checkoutMutate.mockReset()
  push.mockReset()
  cartData.value = {
    items: [{ item_id: 1, quantity: 1, unit_price: '10.00', total: '10.00' }],
    total: '10.00',
  }
  itemStock.value = new Map<number, { stock: number }>([[1, { stock: 10 }]])
})

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('CheckoutView name at payment', () => {
  it('refuses to pay without a name and shows an error', async () => {
    const wrapper = mountView()

    await payButton(wrapper).trigger('click')

    expect(checkoutMutate).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Please enter your name')
  })

  it('sends the typed name with the checkout, paid by default', async () => {
    const wrapper = mountView()

    await wrapper.find('input').setValue('Ana Paula')
    await payButton(wrapper).trigger('click')

    expect(checkoutMutate).toHaveBeenCalledTimes(1)
    expect(checkoutMutate.mock.calls[0][0]).toMatchObject({
      customerName: 'Ana Paula',
      orderType: 'EAT_IN',
      paymentMethod: 'PIX',
      paymentStatus: 'PAID',
    })
  })
})

describe('CheckoutView stock guard', () => {
  it('blocks payment when a line exceeds stock and explains why', async () => {
    cartData.value = {
      items: [{ item_id: 1, quantity: 30, unit_price: '10.00', total: '300.00' }],
      total: '300.00',
    }
    itemStock.value = new Map<number, { stock: number }>([[1, { stock: 2 }]])
    const wrapper = mountView()

    await wrapper.find('input').setValue('Ana Paula')
    await payButton(wrapper).trigger('click')

    expect(checkoutMutate).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Only 2 left of Coffee')
  })
})

describe('CheckoutView simulated payment', () => {
  it('in debug mode lets the terminal pick the outcome', async () => {
    vi.stubEnv('VITE_DEBUG', 'true')
    const wrapper = mountView()

    await wrapper.find('input').setValue('Ana Paula')
    await payButton(wrapper).trigger('click')
    expect(checkoutMutate).not.toHaveBeenCalled()

    await terminalButton(wrapper, 'Approved').trigger('click')

    expect(checkoutMutate).toHaveBeenCalledTimes(1)
    expect(checkoutMutate.mock.calls[0][0]).toMatchObject({ paymentStatus: 'PAID' })
  })

  it('sends a declined outcome and shows the failed terminal with retry', async () => {
    vi.stubEnv('VITE_DEBUG', 'true')
    checkoutMutate.mockImplementation((_input: unknown, opts: { onError?: (e: Error) => void }) => {
      opts.onError?.(new ApiError(400, 'Payment declined'))
    })
    const wrapper = mountView()

    await wrapper.find('input').setValue('Ana Paula')
    await payButton(wrapper).trigger('click')
    await terminalButton(wrapper, 'Declined').trigger('click')

    expect(checkoutMutate.mock.calls[0][0]).toMatchObject({ paymentStatus: 'FAILED' })
    expect(wrapper.text()).toMatch(/try again/i)

    // Retry returns to the outcome picker (debug mode).
    await terminalButton(wrapper, 'Try again').trigger('click')
    expect(wrapper.text()).toContain('Approved')
  })
})
