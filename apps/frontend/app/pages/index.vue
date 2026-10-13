<!-- Day 12: personalizovana početna strana (GET /ml/platform/homepage) sa graceful fallback-om. -->
<template>
  <div class="px-10 py-6">
    <h1 class="text-3xl font-bold mb-2">DM Shop</h1>
    <UCard v-if="home?.hero" class="mb-6" data-testid="home-hero">
      <p class="text-lg">{{ home.hero.content }}</p>
      <p class="text-xs text-muted mt-2">{{ home.hero.module_class }} · {{ home.hero.source }}
        <span v-if="home.hero.fallback">(fallback: {{ home.hero.fallback_reason }})</span></p>
    </UCard>
    <p v-else-if="loaded" class="text-muted mb-6" data-testid="home-fallback">Personalizacija nedostupna — prikazujemo katalog.</p>
    <div v-if="home?.profile" class="flex gap-2 mb-4 text-sm">
      <UBadge variant="subtle">user {{ home.user_id }}</UBadge>
      <UBadge variant="subtle">segment: {{ home.profile.segment?.label }}</UBadge>
      <UBadge variant="subtle">RFM: {{ home.profile.rfm?.bucket ?? '—' }}</UBadge>
      <UBadge variant="subtle">p(buy): {{ home.profile.conversion?.probability }}</UBadge>
    </div>
    <RecSection title="Recommended for you" source="platform" :items="recs" :fallback="recFallback" />
    <div class="mt-8 flex gap-4">
      <UButton to="/shop">Shop</UButton><UButton to="/category" variant="outline">Categories</UButton>
      <UButton to="/search" variant="outline">Search</UButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Rec } from '~/types/Product'
const home = ref<any>(null); const recs = ref<Rec[]>([]); const recFallback = ref(false); const loaded = ref(false)
onMounted(async () => {
  const r = await mlGet<any>(`/platform/homepage?user_id=${getDemoUserId()}&session_id=${getOrGenerateSessionId()}&limit=5`)
  loaded.value = true
  if (!r) return
  home.value = r
  recs.value = enrich(r.recommendations?.recommendations, (await useCatalog()).value)
  recFallback.value = !!r.recommendations?.fallback
})
</script>
