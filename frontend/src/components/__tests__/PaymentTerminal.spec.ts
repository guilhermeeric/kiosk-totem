import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import PaymentTerminal from '../PaymentTerminal.vue'

function mountTerminal(
  overrides: Partial<{
    amount: string
    method: string
    debug: boolean
    state: 'pick' | 'processing' | 'approved' | 'declined'
  }> = {},
) {
  return mount(PaymentTerminal, {
    props: {
      amount: '10.00',
      method: 'PIX',
      debug: false,
      state: 'processing',
      ...overrides,
    },
  })
}

describe('PaymentTerminal', () => {
  it('shows the simulated outcome buttons in debug mode', () => {
    const wrapper = mountTerminal({ debug: true, state: 'pick' })

    expect(wrapper.text()).toContain('Approved')
    expect(wrapper.text()).toContain('Declined')
    expect(wrapper.text()).toContain('Network error')
  })

  it('emits PAID when Approved is chosen', async () => {
    const wrapper = mountTerminal({ debug: true, state: 'pick' })

    const approved = wrapper.findAll('button').find((b) => b.text().includes('Approved'))
    await approved!.trigger('click')

    expect(wrapper.emitted('choose')?.[0]).toEqual(['PAID'])
  })

  it('emits FAILED when a failure is chosen', async () => {
    const wrapper = mountTerminal({ debug: true, state: 'pick' })

    const network = wrapper.findAll('button').find((b) => b.text().includes('Network error'))
    await network!.trigger('click')

    expect(wrapper.emitted('choose')?.[0]).toEqual(['FAILED'])
  })

  it('renders the approved state', () => {
    const wrapper = mountTerminal({ state: 'approved' })

    expect(wrapper.text()).toContain('Approved')
  })

  it('renders the declined state with a retry hint', () => {
    const wrapper = mountTerminal({ state: 'declined' })

    expect(wrapper.text()).toContain('declined')
    expect(wrapper.text()).toMatch(/try again/i)
  })
})
