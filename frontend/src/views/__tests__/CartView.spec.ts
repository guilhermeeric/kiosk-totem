import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { computed, ref } from 'vue'

import CartView from '../CartView.vue'

const applyCouponMutate = vi.fn()
const applyCouponError = ref<Error | null>(null)
const removeCouponMutate = vi.fn()
const push = vi.fn()

const cartData = ref<{
  items: { item_id: number; quantity: number; unit_price: string; total: string }[]
  total: string
  subtotal: string
  coupon_code: string | null
  discount: string
}>({
  items: [{ item_id: 1, quantity: 1, unit_price: '10.00', total: '10.00' }],
  total: '10.00',
  subtotal: '10.00',
  coupon_code: null,
  discount: '0.00',
})
const itemStock = ref(new Map<number, { stock: number }>([[1, { stock: 10 }]]))

vi.mock('../../composables/useItems', () => ({
  useItems: () => ({
    name: (itemId: number) => (itemId === 1 ? 'Coffee' : `Item #${itemId}`),
    byId: computed(() => itemStock.value),
  }),
}))

vi.mock('../../composables/useCart', () => ({
  useCart: () => ({
    cartQuery: { data: cartData, isPending: ref(false) },
    removeItem: { mutate: vi.fn() },
    updateQuantity: { mutate: vi.fn() },
    applyCoupon: { mutate: applyCouponMutate, isPending: ref(false), error: applyCouponError },
    removeCoupon: { mutate: removeCouponMutate },
  }),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

function mountView() {
  return mount(CartView, {
    global: { stubs: { CartLine: true } },
  })
}

function applyButton(wrapper: ReturnType<typeof mountView>) {
  const btn = wrapper.findAll('button').find((b) => b.text().toLowerCase().includes('apply'))
  if (!btn) throw new Error('Apply button not found')
  return btn
}

beforeEach(() => {
  applyCouponMutate.mockReset()
  removeCouponMutate.mockReset()
  push.mockReset()
  applyCouponError.value = null
  cartData.value = {
    items: [{ item_id: 1, quantity: 1, unit_price: '10.00', total: '10.00' }],
    total: '10.00',
    subtotal: '10.00',
    coupon_code: null,
    discount: '0.00',
  }
})

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('CartView coupon entry', () => {
  it('applies the typed code on Apply', async () => {
    const wrapper = mountView()

    await wrapper.find('input[placeholder="Coupon code"]').setValue('welcome10')
    await applyButton(wrapper).trigger('click')

    expect(applyCouponMutate).toHaveBeenCalledTimes(1)
    expect(applyCouponMutate).toHaveBeenCalledWith('welcome10')
  })

  it('surfaces the backend error message', async () => {
    applyCouponError.value = new Error("Coupon 'OLD10' expired at ...")
    const wrapper = mountView()

    expect(wrapper.text()).toContain("Coupon 'OLD10' expired at ...")
  })

  it('does not offer the input once a coupon is applied', async () => {
    cartData.value.coupon_code = 'WELCOME10'
    cartData.value.discount = '5.00'
    cartData.value.total = '5.00'
    const wrapper = mountView()

    expect(wrapper.find('input[placeholder="Coupon code"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('WELCOME10')
  })

  it('removes the applied coupon', async () => {
    cartData.value.coupon_code = 'WELCOME10'
    cartData.value.discount = '5.00'
    cartData.value.total = '5.00'
    const wrapper = mountView()

    const remove = wrapper.findAll('button').find((b) => b.text().toLowerCase().includes('remove'))
    if (!remove) throw new Error('Remove coupon button not found')
    await remove.trigger('click')

    expect(removeCouponMutate).toHaveBeenCalledTimes(1)
  })
})

describe('CartView discount summary', () => {
  it('shows subtotal, coupon discount and discounted total', async () => {
    cartData.value.coupon_code = 'WELCOME10'
    cartData.value.discount = '5.00'
    cartData.value.total = '5.00'
    const wrapper = mountView()

    expect(wrapper.text()).toContain('Subtotal')
    expect(wrapper.text()).toContain('Coupon (WELCOME10)')
    expect(wrapper.text()).toMatch(/5,00/)
  })
})
