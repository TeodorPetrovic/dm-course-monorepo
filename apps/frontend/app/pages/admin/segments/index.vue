<!-- Day 2: segmentacija — trening, profili segmenata, manual RFM vs K-Means. -->
<template>
  <div class="p-6">
    <div class="flex items-center gap-4 mb-4">
      <h1 class="text-2xl font-bold">Customer segments</h1>
      <UInput v-model.number="k" type="number" class="w-20" />
      <UButton :loading="busy" @click="train" data-testid="train-segments">Treniraj (k={{ k }})</UButton>
    </div>
    <MlUnavailable v-if="down" />
    <UAlert v-else-if="!meta" color="info" variant="subtle" title="Model nije treniran"
      description="Kliknite „Treniraj“ (POST /ml/segments/train)." class="mb-4" data-testid="untrained" />
    <p v-if="err" class="text-error mb-2">{{ err }}</p>
    <template v-if="meta">
      <p class="mb-2 text-sm">k={{ meta.k }} · silhouette={{ meta.silhouette }} · korisnika={{ meta.n_customers }} · referenca {{ meta.reference }}</p>
      <UTable :data="meta.segments" :columns="segCols" class="mb-6" data-testid="segments-table" />
      <template v-if="meta.comparison">
        <h2 class="text-xl font-bold mb-2">Manual RFM vs K-Means (ARI = {{ meta.comparison.ari }})</h2>
        <UTable :data="dominant" :columns="domCols" />
      </template>
    </template>
  </div>
</template>
<script lang="ts" setup>
definePageMeta({ layout: 'admin' })
const k = ref(4); const meta = ref<any>(null); const busy = ref(false); const err = ref(""); const down = ref(false)
const segCols = ['segment', 'count', 'share', 'recency_days', 'frequency', 'monetary', 'aov', 'conversion', 'profile']
  .map(x => ({ accessorKey: x, header: x }))
const domCols = ['bucket', 'cluster', 'share', 'count'].map(x => ({ accessorKey: x, header: x }))
const dominant = computed(() => Object.entries(meta.value?.comparison?.dominant_cluster || {}).map(([b, v]: any) => ({ bucket: b, ...v })))
async function load() {
  try { meta.value = await $fetch('/ml/segments'); down.value = false }
  catch (e: any) { meta.value = null; down.value = !(e?.statusCode === 503 || e?.status === 503) }
}
async function train() {
  busy.value = true
  const r = await mlPost('/segments/train', { k: k.value })
  busy.value = false; err.value = r.error || ""
  if (r.data) meta.value = r.data
}
onMounted(load)
</script>
