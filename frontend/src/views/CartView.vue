<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'

import { formatMoney } from '../domain/money'
import { overstockedLines } from '../domain/stock'
import { useCart } from '../composables/useCart'
import { useItems } from '../composables/useItems'
import CartLine from '../components/CartLine.vue'

const router = useRouter()
const { cartQuery, removeItem, updateQuantity } = useCart()
const { byId } = useItems()

const cart = cartQuery.data

// Advisory per-line availability: shows when the cart holds more than the
// current stock (someone else may have bought the rest). The authoritative
// gate is the backend's consume_stock at checkout.
const overstocked = computed(() => overstockedLines(cart.value?.items ?? [], byId.value))

function warningFor(line: { item_id: number }): string | undefined {
  const found = overstocked.value.find((o) => o.itemId === line.item_id)
  return found ? `Only ${found.available} left — ${found.quantity} in your cart` : undefined
}
</script>

<template>
  <div class="mx-auto flex min-h-screen max-w-md flex-col p-6">
    <header class="mb-6 flex items-center gap-3">
      <button
        class="rounded-full bg-muted p-2.5 text-foreground transition hover:bg-accent"
        aria-label="Back to menu"
        @click="router.push({ name: 'menu' })"
      >
        <ArrowLeft class="h-6 w-6" />
      </button>
      <h1 class="text-2xl font-bold">Your cart</h1>
    </header>

    <p v-if="cartQuery.isPending.value" class="text-muted-foreground">Loading...</p>
    <p v-else-if="cart?.items.length === 0" class="text-muted-foreground">
      Your cart is empty.
    </p>

    <div v-else class="flex flex-col gap-3">
      <div
        v-for="line in cart?.items"
        :key="line.item_id"
        class="flex flex-col gap-1"
      >
        <CartLine
          :line="line"
          @increment="(id: number) => updateQuantity.mutate({ itemId: id, quantity: line.quantity + 1 })"
          @decrement="(id: number) => updateQuantity.mutate({ itemId: id, quantity: line.quantity - 1 })"
          @remove="(id: number) => removeItem.mutate(id)"
        />
        <p v-if="warningFor(line)" class="text-sm font-semibold text-destructive">
          {{ warningFor(line) }}
        </p>
      </div>

      <div class="mt-4 flex items-center justify-between border-t border-border pt-4">
        <span class="text-lg">Total</span>
        <span class="text-2xl font-bold">{{ formatMoney(cart?.total ?? '0') }}</span>
      </div>

      <button
        class="mt-4 rounded-xl bg-amber-500 py-4 text-xl font-semibold text-zinc-950 transition hover:bg-amber-400"
        @click="router.push({ name: 'checkout' })"
      >
        Review and pay
      </button>
    </div>
  </div>
</template>
