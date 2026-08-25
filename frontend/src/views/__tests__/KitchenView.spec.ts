import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'

import KitchenView from '../KitchenView.vue'

const { mockOrder, mockUpdateStatus } = vi.hoisted(() => ({
  mockOrder: {
    id: 7,
    status: 'PENDING',
    customer_name: 'Mayhem',
    order_type: 'EAT_IN',
    total: '5.00',
    created_at: new Date().toISOString(),
    items: [{ item_id: 1, quantity: 1, unit_price: '5.00', total: '5.00' }],
    payments: [],
  },
  mockUpdateStatus: vi.fn(),
}))
const mockTransitionPending = ref(false)

vi.mock('@tanstack/vue-query', () => ({
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  useQuery: (options: { queryKey: string[] }) => ({
    data: ref(options.queryKey[1] === 'PENDING' ? [mockOrder] : []),
    isPending: ref(false),
  }),
  useMutation: () => ({
    mutate: (input: unknown) => {
      mockTransitionPending.value = true
      mockUpdateStatus(input)
    },
    isPending: mockTransitionPending,
  }),
}))

vi.mock('../../api/client', () => ({
  api: {
    listOrders: vi.fn(),
    updateOrderStatus: mockUpdateStatus,
  },
}))

vi.mock('../../composables/useItems', () => ({
  useItems: () => ({ name: () => 'Coffee' }),
}))

beforeEach(() => {
  mockUpdateStatus.mockReset()
  mockTransitionPending.value = false
})

describe('KitchenView transitions', () => {
  it('moves a pending order to PREPARING with the right payload', async () => {
    const wrapper = mount(KitchenView)

    const startBtn = wrapper.findAll('button').find((b) => b.text().includes('Start preparing'))
    expect(startBtn).toBeDefined()
    await startBtn!.trigger('click')

    expect(mockUpdateStatus).toHaveBeenCalledTimes(1)
    expect(mockUpdateStatus).toHaveBeenCalledWith({ orderId: 7, status: 'PREPARING' })
  })

  it('disables the transition button while one is in flight — no double transition', async () => {
    const wrapper = mount(KitchenView)

    const startBtn = wrapper.findAll('button').find((b) => b.text().includes('Start preparing'))
    await startBtn!.trigger('click')

    expect(mockUpdateStatus).toHaveBeenCalledTimes(1)
    expect(startBtn!.attributes('disabled')).toBeDefined()
  })
})
