<!-- Day 1: provera tracking-a — poslednji događaji iz lokalne baze + broj po tipu. -->
<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Events</h1>
    <p v-if="error" class="text-error">{{ error }}</p>
    <div class="flex flex-wrap gap-2 mb-4" data-testid="event-counts">
      <UBadge v-for="c in data?.counts" :key="c.event_type" variant="subtle">{{ c.event_type }}: {{ c.n }}</UBadge>
    </div>
    <UTable :data="data?.events || []" :columns="cols" />
  </div>
</template>
<script lang="ts" setup>
definePageMeta({ layout: 'admin' })
const cols = ['event_id', 'event_type', 'user_id', 'user_session', 'product_id', 'category_id', 'price', 'quantity',
  'source', 'timestamp', 'recommendation_source', 'recommendation_position'].map(k => ({ accessorKey: k, header: k }))
const { data, error } = await useFetch<any>('/api/event?limit=50')
</script>
