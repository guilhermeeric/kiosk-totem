<script setup lang="ts">
import { ref } from 'vue'
import { useMutation } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { UtensilsCrossed } from 'lucide-vue-next'

import { api } from '../api/client'
import { useSession } from '../composables/useSession'

const router = useRouter()
const { setSession } = useSession()

const name = ref('')
const error = ref('')

const createCart = useMutation({
  mutationFn: (customerName: string) =>
    api.createCart(crypto.randomUUID()).then((cart) => ({ cart, customerName })),
  onSuccess: ({ cart, customerName }) => {
    setSession(cart.session_id, customerName)
    router.push({ name: 'menu' })
  },
  onError: (err: Error) => {
    error.value = err.message
  },
})

function start() {
  if (!name.value.trim()) {
    error.value = 'Please enter your name'
    return
  }
  createCart.mutate(name.value.trim())
}
</script>

<template>
  <div
    class="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-6 bg-gradient-to-b from-amber-50 to-background p-6"
  >
    <div class="flex flex-col items-center gap-3 text-center">
      <div class="rounded-full bg-amber-500 p-5 shadow-lg shadow-amber-500/30">
        <UtensilsCrossed class="h-12 w-12 text-zinc-950" />
      </div>
      <h1 class="text-5xl font-black tracking-tight">Totem</h1>
      <p class="text-lg text-muted-foreground">Order your food in seconds</p>
    </div>

    <input
      v-model="name"
      autofocus
      class="w-full rounded-xl border border-input bg-card px-4 py-4 text-lg shadow-sm outline-none ring-amber-500 transition placeholder:text-muted-foreground focus:ring-2"
      placeholder="Your name"
      @keyup.enter="start"
    />
    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <button
      class="w-full rounded-xl bg-amber-500 py-5 text-xl font-semibold text-zinc-950 transition hover:bg-amber-400 disabled:opacity-50"
      :disabled="createCart.isPending.value"
      @click="start"
    >
      {{ createCart.isPending.value ? 'Starting...' : 'Start' }}
    </button>
  </div>
</template>
