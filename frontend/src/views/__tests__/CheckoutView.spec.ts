import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { computed, ref } from 'vue'

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

beforeEach(() => {
  checkoutMutate.mockReset()
  push.mockReset()
  cartData.value = {
    items: [{ item_id: 1, quantity: 1, unit_price: '10.00', total: '10.00' }],
    total: '10.00',
  }
  itemStock.value = new Map<number, { stock: number }>([[1, { stock: 10 }]])
})

describe('CheckoutView name at payment', () => {
  it('refuses to pay without a name and shows an error', async () => {
    const wrapper = mountView()

    await payButton(wrapper).trigger('click')

    expect(checkoutMutate).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Please enter your name')
  })

  it('sends the typed name with the checkout', async () => {
    const wrapper = mountView()

    await wrapper.find('input').setValue('Ana Paula')
    await payButton(wrapper).trigger('click')

    expect(checkoutMutate).toHaveBeenCalledTimes(1)
    expect(checkoutMutate.mock.calls[0][0]).toMatchObject({
      customerName: 'Ana Paula',
      orderType: 'EAT_IN',
      paymentMethod: 'PIX',
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

  it('allows payment when quantities are within stock', async () => {
    const wrapper = mountView()

    await wrapper.find('input').setValue('Ana Paula')
    await payButton(wrapper).trigger('click')

    expect(checkoutMutate).toHaveBeenCalledTimes(1)
  })
})
