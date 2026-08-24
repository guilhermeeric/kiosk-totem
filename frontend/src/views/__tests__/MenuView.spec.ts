import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'

import MenuView from '../MenuView.vue'

const push = vi.fn()
const cartData = ref<{
  session_id: string
  items: { item_id: number; quantity: number }[]
  total: string
  handed_off_at?: string | null
}>({
  session_id: 'sess-1',
  items: [],
  total: '0',
  handed_off_at: null,
})

vi.mock('../../composables/useItems', () => ({
  useItems: () => ({ itemsQuery: { data: ref([]), isPending: ref(false) } }),
}))

vi.mock('../../composables/useCart', () => ({
  useCart: () => ({
    cartQuery: { data: cartData, isPending: ref(false) },
    addItem: { mutate: vi.fn() },
  }),
}))

vi.mock('../../composables/useSession', () => ({
  useSession: () => ({ sessionId: ref('sess-1') }),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

function mountView() {
  return mount(MenuView)
}

function handoffButton(wrapper: ReturnType<typeof mountView>) {
  return wrapper.findAll('button').find((b) => b.text().includes('Continue on phone'))
}

beforeEach(() => {
  cartData.value = { session_id: 'sess-1', items: [], total: '0', handed_off_at: null }
})

describe('MenuView handoff trigger', () => {
  it('offers handoff on the kiosk, before the session is handed off', () => {
    const wrapper = mountView()

    expect(handoffButton(wrapper)).toBeDefined()
  })

  it('hides handoff on a phone that already adopted the session', () => {
    cartData.value = {
      session_id: 'sess-1',
      items: [],
      total: '0',
      handed_off_at: '2026-01-01T00:00:00',
    }
    const wrapper = mountView()

    expect(handoffButton(wrapper)).toBeUndefined()
  })
})
