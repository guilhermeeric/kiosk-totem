import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'

import TrackView from '../TrackView.vue'

const { useOrder } = vi.hoisted(() => ({ useOrder: vi.fn() }))

const orderRef = ref<{
  id: number
  customer_name: string
  order_type: string
  status: string
} | null>(null)
const isPending = ref(false)
const errorRef = ref<unknown>(null)

vi.mock('../../composables/useOrder', () => ({ useOrder }))

function mountView() {
  return mount(TrackView, { props: { id: '42' } })
}

beforeEach(() => {
  orderRef.value = null
  isPending.value = false
  errorRef.value = null
  useOrder.mockClear()
  useOrder.mockReturnValue({ data: orderRef, isPending, error: errorRef })
})

describe('TrackView', () => {
  it('polls the order every 5 seconds for live status', () => {
    mountView()
    expect(useOrder).toHaveBeenCalledWith(42, 5000)
  })

  it('shows a loading state while the order is fetching', () => {
    isPending.value = true
    const wrapper = mountView()
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows not-found when the order cannot be fetched', () => {
    errorRef.value = new Error('404')
    const wrapper = mountView()
    expect(wrapper.text()).toContain('Order not found')
  })

  it('renders the order number and customer', () => {
    orderRef.value = {
      id: 42,
      customer_name: 'Ana',
      order_type: 'EAT_IN',
      status: 'PREPARING',
    }
    const wrapper = mountView()
    expect(wrapper.text()).toContain('42')
    expect(wrapper.text()).toContain('Ana')
  })

  it('shows the status label and its progress step', () => {
    orderRef.value = {
      id: 42,
      customer_name: 'Ana',
      order_type: 'EAT_IN',
      status: 'PREPARING',
    }
    const wrapper = mountView()
    expect(wrapper.text()).toContain('Being prepared')
    // step 1 of 4 filled (PREPARING) — two active segments
    expect(wrapper.findAll('.bg-amber-500')).toHaveLength(2)
  })

  it('renders the full progress bar when ready', () => {
    orderRef.value = {
      id: 42,
      customer_name: 'Ana',
      order_type: 'EAT_IN',
      status: 'READY',
    }
    const wrapper = mountView()
    expect(wrapper.text()).toContain('Ready — come pick up!')
    expect(wrapper.findAll('.bg-amber-500')).toHaveLength(3)
  })

  it('shows the cancelled state without progress segments', () => {
    orderRef.value = {
      id: 42,
      customer_name: 'Ana',
      order_type: 'EAT_IN',
      status: 'CANCELLED',
    }
    const wrapper = mountView()
    expect(wrapper.text()).toContain('Cancelled')
    expect(wrapper.findAll('.bg-amber-500')).toHaveLength(0)
  })
})
