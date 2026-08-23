<script setup lang="ts">
import { Minus, Plus, Trash2 } from 'lucide-vue-next'

import { formatMoney } from '../domain/money'
import type { components } from '../domain/api'

type CartItem = components['schemas']['CartItemResponse']

defineProps<{ line: CartItem }>()
defineEmits<{
  increment: [itemId: number]
  decrement: [itemId: number]
  remove: [itemId: number]
}>()
</script>

<template>
  <div class="flex items-center gap-4 rounded-xl border border-border bg-card px-4 py-3 shadow-sm">
    <div class="flex-1">
      <p class="font-medium">Item #{{ line.item_id }}</p>
      <p class="text-sm text-muted-foreground">
        {{ line.quantity }} x {{ formatMoney(line.unit_price) }}
      </p>
    </div>
    <p class="font-semibold">{{ formatMoney(line.total) }}</p>
    <div class="flex items-center gap-1">
      <button
        class="rounded-full bg-muted p-1.5 text-foreground hover:bg-accent"
        aria-label="Decrease"
        @click="$emit('decrement', line.item_id)"
      >
        <Minus class="h-4 w-4" />
      </button>
      <span class="w-8 text-center font-semibold">{{ line.quantity }}</span>
      <button
        class="rounded-full bg-muted p-1.5 text-foreground hover:bg-accent"
        aria-label="Increase"
        @click="$emit('increment', line.item_id)"
      >
        <Plus class="h-4 w-4" />
      </button>
      <button
        class="ml-2 rounded-full bg-red-100 p-1.5 text-red-600 hover:bg-red-200"
        aria-label="Remove"
        @click="$emit('remove', line.item_id)"
      >
        <Trash2 class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
