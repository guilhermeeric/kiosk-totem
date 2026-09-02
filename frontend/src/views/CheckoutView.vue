<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'

import { formatMoney } from '../domain/money'
import { overstockedLines } from '../domain/stock'
import { useCart } from '../composables/useCart'
import { useCheckout } from '../composables/useCheckout'
import { useItems } from '../composables/useItems'
import PaymentTerminal from '../components/PaymentTerminal.vue'

const router = useRouter()
const { cartQuery } = useCart()
const { checkoutMutation } = useCheckout()
const { byId, name } = useItems()

const customerName = ref('')
const orderType = ref<'EAT_IN' | 'TAKEAWAY'>('EAT_IN')
const paymentMethod = ref<'PIX' | 'CREDIT_CARD' | 'DEBIT_CARD' | 'CASH'>('PIX')
const error = ref('')

// Simulated payment terminal. In debug mode the operator picks the outcome;
// otherwise payments always approve.
const isDebug = import.meta.env.VITE_DEBUG === 'true'
const showTerminal = ref(false)
const terminalState = ref<'pick' | 'processing' | 'approved' | 'declined'>('pick')

const cart = cartQuery.data

const total = computed(() => cart.value?.total ?? '0')

// Advisory guard: a line exceeding current stock cannot be paid. The backend
// remains the authority (it catches races the client cannot see).
const overstocked = computed(() => overstockedLines(cart.value?.items ?? [], byId.value))

function pay() {
  error.value = ''
  const trimmedName = customerName.value.trim()
  if (!trimmedName) {
    error.value = 'Please enter your name'
    return
  }
  const first = overstocked.value[0]
  if (first) {
    error.value = `Only ${first.available} left of ${name(first.itemId)} — adjust your cart`
    return
  }

  showTerminal.value = true
  if (!isDebug) runCheckout('PAID')
}

function runCheckout(status: 'PAID' | 'FAILED') {
  error.value = ''
  terminalState.value = 'processing'
  checkoutMutation.mutate(
    {
      customerName: customerName.value.trim(),
      orderType: orderType.value,
      paymentMethod: paymentMethod.value,
      paymentStatus: status,
    },
    {
      onSuccess: (order) => {
        terminalState.value = 'approved'
        window.setTimeout(() => {
          router.push({ name: 'receipt', params: { id: String(order.id) } })
        }, 1500)
      },
      onError: (err: Error) => {
        terminalState.value = 'declined'
        error.value = err.message
      },
    },
  )
}

function onChoose(status: 'PAID' | 'FAILED') {
  runCheckout(status)
}

function onRetry() {
  terminalState.value = 'pick'
  if (!isDebug) runCheckout('PAID')
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

    <template v-else-if="showTerminal">
      <PaymentTerminal
        :amount="total"
        :method="paymentMethod"
        :debug="isDebug"
        :state="terminalState"
        @choose="onChoose"
        @retry="onRetry"
      />
      <p v-if="error" class="text-center text-sm text-destructive">{{ error }}</p>
    </template>

    <template v-else>
      <!-- Full order review: every line item, not just the total -->
      <div class="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 shadow-sm">
        <div v-for="line in cart?.items" :key="line.item_id" class="flex justify-between gap-3">
          <span class="min-w-0 flex-1 truncate">{{ name(line.item_id) }}</span>
          <span class="shrink-0 text-muted-foreground">{{ line.quantity }}x</span>
          <span class="shrink-0 font-medium">{{ formatMoney(line.total) }}</span>
        </div>
        <template v-if="cart?.coupon_code">
          <div class="mt-2 flex justify-between border-t border-border pt-2 text-muted-foreground">
            <span>Subtotal</span>
            <span>{{ formatMoney(cart.subtotal) }}</span>
          </div>
          <div class="flex justify-between text-muted-foreground">
            <span>Coupon ({{ cart.coupon_code }})</span>
            <span>−{{ formatMoney(cart.discount) }}</span>
          </div>
          <div class="flex justify-between text-lg font-bold">
            <span>Total</span>
            <span>{{ formatMoney(total) }}</span>
          </div>
        </template>
        <div
          v-else
          class="mt-2 flex justify-between border-t border-border pt-2 text-lg font-bold"
        >
          <span>Total</span>
          <span>{{ formatMoney(total) }}</span>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <span class="text-muted-foreground">Who's the order for?</span>
        <input
          v-model="customerName"
          autofocus
          class="w-full rounded-xl border border-input bg-card px-4 py-3 text-lg shadow-sm outline-none ring-amber-500 transition placeholder:text-muted-foreground focus:ring-2"
          placeholder="Your name"
          @keyup.enter="pay"
        />
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
