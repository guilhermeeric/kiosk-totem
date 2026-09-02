<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'

import { formatMoney } from '../domain/money'
import { overstockedLines } from '../domain/stock'
import { useCart } from '../composables/useCart'
import { useItems } from '../composables/useItems'
import CartLine from '../components/CartLine.vue'

const router = useRouter()
const { cartQuery, removeItem, updateQuantity, applyCoupon, removeCoupon } = useCart()
const { byId } = useItems()

const cart = cartQuery.data
const couponCode = ref('')

function applyCode() {
  const code = couponCode.value.trim()
  if (!code || applyCoupon.isPending.value) return
  applyCoupon.mutate(code)
  couponCode.value = ''
}

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

      <!-- Coupon: applied chip + remove, or code entry -->
      <div
        v-if="cart?.coupon_code"
        class="flex items-center justify-between gap-3 rounded-xl bg-muted px-4 py-3"
      >
        <p class="min-w-0 truncate text-sm font-semibold">
          Coupon {{ cart.coupon_code }} — {{ formatMoney(cart.discount) }} off
        </p>
        <button
          class="shrink-0 text-sm font-semibold text-destructive transition hover:underline"
          aria-label="Remove coupon"
          @click="removeCoupon.mutate()"
        >
          Remove
        </button>
      </div>
      <div v-else class="flex gap-2">
        <input
          v-model="couponCode"
          class="w-full min-w-0 flex-1 rounded-xl border border-input bg-card px-4 py-3 text-lg shadow-sm outline-none ring-amber-500 transition placeholder:text-muted-foreground focus:ring-2"
          placeholder="Coupon code"
          aria-label="Coupon code"
          @keyup.enter="applyCode"
        />
        <button
          class="shrink-0 rounded-xl bg-muted px-4 font-semibold transition hover:bg-accent disabled:opacity-50"
          :disabled="applyCoupon.isPending.value"
          @click="applyCode"
        >
          Apply
        </button>
      </div>
      <p v-if="!cart?.coupon_code && applyCoupon.error.value" class="text-sm text-destructive">
        {{ applyCoupon.error.value.message }}
      </p>

      <div class="mt-4 border-t border-border pt-4">
        <template v-if="cart?.coupon_code">
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">Subtotal</span>
            <span>{{ formatMoney(cart.subtotal) }}</span>
          </div>
          <div class="flex items-center justify-between text-muted-foreground">
            <span>Coupon ({{ cart.coupon_code }})</span>
            <span>−{{ formatMoney(cart.discount) }}</span>
          </div>
        </template>
        <div class="flex items-center justify-between">
          <span class="text-lg">Total</span>
          <span class="text-2xl font-bold">{{ formatMoney(cart?.total ?? '0') }}</span>
        </div>
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
