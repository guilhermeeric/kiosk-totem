import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { api } from '../../api/client'
import HandoffOverlay from '../HandoffOverlay.vue'

vi.mock('../../api/client', () => ({
  api: {
    getCart: vi.fn(),
  },
}))

const getCart = vi.mocked(api.getCart)

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'start', component: {} },
      { path: '/menu', name: 'menu', component: {} },
    ],
  })
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function mountOverlay(sessionId: string) {
  const router = makeRouter()
  const queryClient = makeQueryClient()
  const wrapper = mount(HandoffOverlay, {
    props: { sessionId },
    global: {
      plugins: [router, [VueQueryPlugin, { queryClient }]],
    },
  })
  return { wrapper, router }
}

beforeEach(() => {
  getCart.mockReset()
})

describe('HandoffOverlay polling', () => {
  it('polls the captured session (not the cleared one) and resets when adopted', async () => {
    vi.useFakeTimers()
    const { wrapper, router } = mountOverlay('sess-1')

    // Not handed off yet.
    getCart.mockResolvedValue({ handed_off_at: null } as never)

    // Confirm the handoff (this clears the totem session).
    await wrapper.findAll('button')[1].trigger('click')
    // Mimic MenuView's ref binding: clearSession() empties the session prop.
    await wrapper.setProps({ sessionId: '' })

    // The phone adopts the session: marker appears on the next poll.
    getCart.mockResolvedValue({ handed_off_at: '2026-01-01T00:00:00' } as never)

    await vi.advanceTimersByTimeAsync(2_100)

    // Regression: the poll must keep hitting the captured session id, never
    // the empty one left by clearSession().
    expect(getCart.mock.calls.length).toBeGreaterThan(0)
    expect(getCart.mock.calls.every(([sid]) => sid === 'sess-1')).toBe(true)

    // The totem closes the overlay and leaves for the start screen.
    expect(wrapper.emitted('close')).toBeTruthy()
    await vi.runOnlyPendingTimersAsync()
    expect(router.currentRoute.value.name).toBe('start')

    vi.useRealTimers()
  })
})
