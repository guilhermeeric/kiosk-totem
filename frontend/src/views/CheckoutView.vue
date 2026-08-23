<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'

import { formatMoney } from '../domain/money'
import { useSession } from '../composables/useSession'
import { useCart } from '../composables/useCart'
import { useCheckout } from '../composables/useCheckout'
import { useItems } from '../composables/useItems'
import { ApiError } from '../api/client'

const router = useRouter()
const { customerName } = useSession()
const { cartQuery } = useCart()
const { checkoutMutation } = useCheckout()
const { name } = useItems()

const orderType = ref<'EAT_IN' | 'TAKEAWAY'>('EAT_IN')
const paymentMethod = ref<'PIX' | 'CREDIT_CARD' | 'DEBIT_CARD' | 'CASH'>('PIX')
const error = ref('')

const cart = cartQuery.data

const total = computed(() => cart.value?.total ?? '0')

function pay() {
  error.value = ''
  checkoutMutation.mutate(
    {
      customerName: customerName.value,
      orderType: orderType.value,
      paymentMethod: paymentMethod.value,
    },
    {
      onSuccess: (order) => {
        router.push({ name: 'receipt', params: { id: String(order.id) } })
      },
      onError: (err: Error) => {
        error.value = err instanceof ApiError ? err.message : 'Checkout failed'
      },
    },
  )
}
</script>

<template>
  <div class="mx-auto flex min-h-screen max-w-md flex-col gap-6 p-6">
    <header class="flex items-center gap-3">
      <button
        class="rounded-full bg-muted p-2.5 text-foreground transition hover:bg-accent"
        aria-label="Back to cart"
        @click="router.push({ name: 'cart' })"
      >
        <ArrowLeft class="h-6 w-6" />
      </button>
      <h1 class="text-2xl font-bold">Review your order</h1>
    </header>

    <p v-if="cartQuery.isPending.value" class="text-muted-foreground">Loading...</p>
    <p v-else-if="cart?.items.length === 0" class="text-muted-foreground">
      Your cart is empty.
      <button class="font-semibold text-amber-600 underline" @click="router.push({ name: 'menu' })">
        Back to menu
      </button>
    </p>

    <template v-else>
      <!-- Full order review: every line item, not just the total -->
      <div class="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 shadow-sm">
        <div v-for="line in cart?.items" :key="line.item_id" class="flex justify-between gap-3">
          <span class="min-w-0 flex-1 truncate">{{ name(line.item_id) }}</span>
          <span class="shrink-0 text-muted-foreground">{{ line.quantity }}x</span>
          <span class="shrink-0 font-medium">{{ formatMoney(line.total) }}</span>
        </div>
        <div class="mt-2 flex justify-between border-t border-border pt-2 text-lg font-bold">
          <span>Total</span>
          <span>{{ formatMoney(total) }}</span>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <span class="text-muted-foreground">Eating here or taking away?</span>
        <div class="grid grid-cols-2 gap-2">
          <button
            class="rounded-xl bg-muted py-3 font-semibold transition hover:bg-accent"
            :class="{ 'ring-2 ring-amber-500': orderType === 'EAT_IN' }"
            @click="orderType = 'EAT_IN'"
          >
            Eat here
          </button>
          <button
            class="rounded-xl bg-muted py-3 font-semibold transition hover:bg-accent"
            :class="{ 'ring-2 ring-amber-500': orderType === 'TAKEAWAY' }"
            @click="orderType = 'TAKEAWAY'"
          >
            Take away
          </button>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <span class="text-muted-foreground">Payment method</span>
        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="m in ['PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'CASH'] as const"
            :key="m"
            class="rounded-xl bg-muted py-3 text-sm font-semibold transition hover:bg-accent"
            :class="{ 'ring-2 ring-amber-500': paymentMethod === m }"
            @click="paymentMethod = m"
          >
            {{ m.replace('_', ' ') }}
          </button>
        </div>
      </div>

      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>

      <button
        class="rounded-xl bg-amber-500 py-5 text-xl font-bold text-zinc-950 transition hover:bg-amber-400 disabled:opacity-50"
        :disabled="checkoutMutation.isPending.value"
        @click="pay"
      >
        {{ checkoutMutation.isPending.value ? 'Paying...' : `Pay ${formatMoney(total)}` }}
      </button>
    </template>
  </div>
</template>
