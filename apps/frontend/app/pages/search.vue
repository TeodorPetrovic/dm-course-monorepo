<!-- Day 10: semantička pretraga (GET /ml/search/semantic?q=...) -->
<template>
  <div class="px-10 py-6">
    <h1 class="text-2xl font-bold mb-4">Search</h1>
    <form class="flex gap-2 mb-4" @submit.prevent="search">
      <UInput v-model="q" placeholder="npr. wireless earbuds for travel" class="w-96" data-testid="search-input" />
      <UButton type="submit">Search</UButton>
    </form>
    <div v-if="res" class="flex gap-2 mb-4" data-testid="search-meta">
      <UBadge variant="subtle">{{ res.method }}</UBadge>
      <UBadge v-if="embedder" variant="subtle">{{ embedder }}</UBadge>
      <UBadge v-if="res.fallback" color="warning">fallback: {{ res.fallback_reason }}</UBadge>
    </div>
    <p v-if="error" class="text-error">{{ error }}</p>
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard v-for="(r, i) in results" :key="r.product_id">
        <NuxtLink :to="`/product/${r.slug}`" @click="trackRecommendationClick(r.product_id, 'semantic', i + 1)">
          <NuxtImg class="w-full h-24 object-cover" :src="r.img_url" />
          <p class="font-bold mt-2 text-sm">{{ r.name }}</p>
          <p class="text-xs text-muted">score {{ r.score }}</p>
          <p class="font-bold">{{ formatPrice(r.price) }}</p>
        </NuxtLink>
      </UCard>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Rec } from '~/types/Product'
const route = useRoute()
const q = ref(String(route.query.q || ""))
const res = ref<any>(null); const error = ref(""); const results = ref<Rec[]>([]); const embedder = ref("")
async function search() {
  if (!q.value.trim()) return
  // TEACH d10: semantička pretraga (GET /search/semantic)
  await trackSearchEvent()
  const r = await mlGet<any>(`/search/semantic?q=${encodeURIComponent(q.value)}&limit=10`)
  if (!r) { error.value = "dm-ml nedostupan — pretraga trenutno ne radi"; results.value = []; return }
  error.value = ""; res.value = r; results.value = enrich(r.results, (await useCatalog()).value)
  embedder.value = r.embedder || ""
  // /TEACH
}
onMounted(() => { if (q.value) search() })
</script>
