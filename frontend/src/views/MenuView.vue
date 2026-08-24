<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowRight, ShoppingBag, Smartphone } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

import type { components } from '../domain/api'
import { formatMoney } from '../domain/money'
import { useItems } from '../composables/useItems'
import { useCart } from '../composables/useCart'
import { useSession } from '../composables/useSession'
import ItemCard from '../components/ItemCard.vue'
import HandoffOverlay from '../components/HandoffOverlay.vue'

type Item = components['schemas']['ItemResponse']

const router = useRouter()
const { itemsQuery } = useItems()
const { cartQuery, addItem } = useCart()
const { sessionId } = useSession()

const showHandoff = ref(false)

const categories = computed(() => {
  const groups = new Map<string, Item[]>()
  for (const item of itemsQuery.data.value ?? []) {
    const list = groups.get(item.category) ?? []
    list.push(item)
    groups.set(item.category, list)
  }
  return [...groups.entries()]
})

const selectedCategory = ref<string | null>(null)

watch(
  categories,
  (groups) => {
    if (!groups.length) return
    const names = groups.map(([name]) => name)
    if (selectedCategory.value == null || !names.includes(selectedCategory.value)) {
      selectedCategory.value = names[0]
    }
  },
  { immediate: true },
)

const visibleItems = computed(() => {
  const group = categories.value.find(([name]) => name === selectedCategory.value)
  return group?.[1] ?? []
})

const itemCount = computed(
  () => cartQuery.data.value?.items.reduce((sum, line) => sum + line.quantity, 0) ?? 0,
)

const cartTotal = computed(() => cartQuery.data.value?.total ?? '0')

// The cart marker is the role signal: null = kiosk (handoff offered),
// set = already on a phone (no recursive continue-on-phone).
const isHandedOff = computed(() => cartQuery.data.value?.handed_off_at != null)
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden bg-background">
    <!-- Header + category pills (vertical-minded: top → categories → items → checkout) -->
    <header class="border-b border-border bg-card px-6 pt-4">
      <div class="flex items-center gap-2 pb-3">
        <ShoppingBag class="h-6 w-6 text-amber-500" />
        <span class="text-xl font-bold">Totem</span>
        <button
          v-if="!isHandedOff"
          class="ml-auto flex items-center gap-2 rounded-full bg-muted px-4 py-2 text-sm font-semibold transition hover:bg-accent"
          @click="showHandoff = true"
        >
          <Smartphone class="h-4 w-4" />
          Continue on phone
        </button>
      </div>
      <nav class="-mx-6 flex gap-2 overflow-x-auto px-6 pb-3">
        <template v-if="itemsQuery.isPending.value">
          <div v-for="i in 4" :key="i" class="h-11 w-28 shrink-0 animate-pulse rounded-full bg-muted" />
        </template>
        <button
          v-for="[name] in categories"
          v-else
          :key="name"
          class="shrink-0 whitespace-nowrap rounded-full px-5 py-2.5 text-lg font-semibold capitalize transition"
          :class="
            name === selectedCategory
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-foreground/70 hover:bg-accent hover:text-foreground'
          "
          @click="selectedCategory = name"
        >
          {{ name }}
        </button>
      </nav>
    </header>

    <!-- Items of the selected category -->
    <main class="flex-1 overflow-y-auto p-6">
      <template v-if="itemsQuery.isPending.value">
        <div class="grid grid-cols-2 gap-4">
          <div v-for="i in 6" :key="i" class="h-28 animate-pulse rounded-2xl bg-muted" />
        </div>
      </template>
      <template v-else>
        <div class="grid grid-cols-2 gap-4 pb-4">
          <ItemCard
            v-for="item in visibleItems"
            :key="item.id"
            :item="item"
            @add="(itemId: number) => addItem.mutate({ itemId, quantity: 1 })"
          />
        </div>
      </template>
    </main>

    <!-- Big checkout bar -->
    <footer
      v-if="itemCount > 0"
      class="flex items-center justify-between gap-4 border-t border-border bg-card px-6 py-4"
    >
      <div class="flex flex-col">
        <span class="text-sm text-muted-foreground">
          {{ itemCount }} {{ itemCount === 1 ? 'item' : 'items' }}
        </span>
        <span class="text-2xl font-bold">{{ formatMoney(cartTotal) }}</span>
      </div>
      <button
        class="flex items-center gap-2 rounded-2xl bg-amber-500 px-10 py-5 text-2xl font-bold text-zinc-950 transition hover:bg-amber-400"
        @click="router.push({ name: 'cart' })"
      >
        Checkout
        <ArrowRight class="h-7 w-7" />
      </button>
    </footer>

    <HandoffOverlay
      v-if="showHandoff"
      :session-id="sessionId"
      @close="showHandoff = false"
    />
  </div>
</template>
