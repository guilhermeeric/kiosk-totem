<script setup lang="ts">
import { Plus } from 'lucide-vue-next'

import { formatMoney } from '../domain/money'
import type { components } from '../domain/api'

type Item = components['schemas']['ItemResponse']

defineProps<{ item: Item }>()
defineEmits<{ add: [itemId: number] }>()
</script>

<template>
  <div class="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 shadow-sm">
    <div class="flex items-start justify-between gap-2">
      <div>
        <h3 class="text-lg font-semibold">{{ item.name }}</h3>
        <p class="text-sm text-muted-foreground">{{ formatMoney(item.price) }}</p>
      </div>
      <button
        class="rounded-full bg-amber-500 p-2.5 text-zinc-950 transition hover:bg-amber-400"
        :aria-label="`Add ${item.name}`"
        @click="$emit('add', item.id)"
      >
        <Plus class="h-6 w-6" />
      </button>
    </div>
  </div>
</template>
