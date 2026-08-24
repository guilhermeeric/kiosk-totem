import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import ItemCard from '../ItemCard.vue'

type Item = {
  id: number
  name: string
  price: string
  category: string
  icon: string
  stock: number
}

function makeItem(overrides: Partial<Item> = {}): Item {
  return { id: 1, name: 'Burger', price: '9.99', category: 'savory', icon: 'burger', stock: 5, ...overrides }
}

describe('ItemCard stock', () => {
  it('disables add and shows out of stock when stock is 0', () => {
    const wrapper = mount(ItemCard, { props: { item: makeItem({ stock: 0 }) } })

    expect(wrapper.text()).toContain('Out of stock')
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('emits add when stock is available', async () => {
    const wrapper = mount(ItemCard, { props: { item: makeItem({ stock: 2 }) } })

    await wrapper.find('button').trigger('click')

    expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
    expect(wrapper.emitted('add')?.[0]).toEqual([1])
  })
})
