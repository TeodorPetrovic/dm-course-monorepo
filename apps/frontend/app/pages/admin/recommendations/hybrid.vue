<!-- Day 8: user-based evaluacija hybrid pipeline-a vs pojedinačni izvori. -->
<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Hybrid recommender (user-based evaluacija)</h1>
    <MlUnavailable v-if="!rep && loaded" />
    <template v-if="rep">
      <p class="text-sm mb-2">split {{ rep.split_time }} · test korisnika {{ rep.n_test_users }} · K={{ rep.k }}</p>
      <UTable :data="rep.comparison" :columns="cols" data-testid="hybrid-table" />
      <p class="text-xs text-muted mt-2">Težine spajanja (0.2/0.3/0.3/0.2) su ručno izabrane heuristike, ne naučene.</p>
    </template>
  </div>
</template>
<script lang="ts" setup>
definePageMeta({ layout: 'admin' })
const rep = ref<any>(null); const loaded = ref(false)
const cols = ['method', 'precision_at_k', 'recall_at_k', 'hit_rate_at_k', 'ndcg_at_k', 'catalog_coverage'].map(x => ({ accessorKey: x, header: x }))
onMounted(async () => {
  // TEACH d08: user-based evaluacija hybrid vs izvori
  rep.value = await mlGet('/analytics/recommendations/hybrid')
  // /TEACH
  loaded.value = true
})
</script>
