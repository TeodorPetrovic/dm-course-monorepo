<!-- Sekcija preporuka: loguje impresije (jednom) i klikove sa recommendation_source + pozicijom (Day 1/9). -->
<template>
  <div v-if="items.length" class="mt-10" :data-testid="`rec-${source}`">
    <div class="flex items-center gap-2 mb-4">
      <h2 class="text-2xl font-bold">{{ title }}</h2>
      <UBadge variant="subtle">{{ source }}</UBadge>
      <UBadge v-if="fallback" color="warning" variant="subtle">showing popularity fallback</UBadge>
      <span v-if="note" class="text-sm text-muted">{{ note }}</span>
    </div>
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard v-for="(rec, i) in items" :key="rec.product_id">
        <NuxtLink :to="`/product/${rec.slug}`" @click="trackRecommendationClick(rec.product_id, source, i + 1)">
          <NuxtImg class="w-full h-24 object-cover" :src="rec.img_url" />
          <p class="font-bold mt-2 text-sm">{{ rec.name }}</p>
          <p class="text-xs text-gray-600">{{ rec.description?.substring(0, 50) }}</p>
          <p class="font-bold mt-1">{{ formatPrice(rec.price) }}</p>
        </NuxtLink>
      </UCard>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Rec } from '~/types/Product'
const props = defineProps<{ title: string, source: string, items: Rec[], fallback?: boolean, note?: string }>()
watch(() => props.items, (items) => {
  items.forEach((r, i) => trackRecommendationImpression(r.product_id, props.source, i + 1))
}, { immediate: true })
</script>
