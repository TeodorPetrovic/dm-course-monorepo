<!-- Day 4: kampanje — preporučena publika (rule vs ML) sa razlozima + targeting-comparison. -->
<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Campaigns</h1>
    <MlUnavailable v-if="down" />
    <UTable v-else :data="campaigns" :columns="cCols" class="mb-4" data-testid="campaigns-table" />
    <div class="flex gap-2 items-center mb-4">
      <USelect v-model="cid" :items="campaigns.map((c: any) => ({ label: c.name, value: c.campaign_id }))" class="w-72" />
      <UButtonGroup>
        <UButton :variant="mode === 'ml' ? 'solid' : 'outline'" @click="mode = 'ml'">ML</UButton>
        <UButton :variant="mode === 'rule' ? 'solid' : 'outline'" @click="mode = 'rule'">Rule</UButton>
      </UButtonGroup>
      <UButton @click="loadAudience" data-testid="load-audience">Prikaži publiku</UButton>
    </div>
    <UAlert v-if="aud?.fallback" color="warning" variant="subtle" class="mb-2"
      :title="`Publika je rule-based (fallback: ${aud.fallback_reason})`"
      description="Trenirajte modele na stranicama Segments (Day 2) i Conversion (Day 3)." />
    <p v-if="aud" class="text-sm mb-2" data-testid="audience-summary">{{ aud.campaign_name }} · mode {{ aud.mode }} ·
      kandidata {{ aud.total_candidates }} · izabrano {{ aud.selected }} · prikazano {{ aud.returned }}</p>
    <UTable v-if="aud" :data="audRows" :columns="aCols" class="mb-6" />
    <template v-if="cmp?.metrics">
      <h2 class="text-xl font-bold mb-2">Rule vs ML</h2>
      <UTable :data="cmpRows" :columns="kCols" data-testid="comparison-table" />
      <p class="text-sm mt-2">lift očekivanih konverzija: {{ cmp.metrics.lift_expected_conversions }} · overlap {{ cmp.metrics.overlap }} · jaccard {{ cmp.metrics.jaccard }}</p>
    </template>
  </div>
</template>
<script lang="ts" setup>
definePageMeta({ layout: 'admin' })
const campaigns = ref<any[]>([]); const down = ref(false); const cid = ref(1); const mode = ref<'ml' | 'rule'>('ml')
const aud = ref<any>(null); const cmp = ref<any>(null)
const cCols = ['campaign_id', 'name', 'target_segments', 'eligible_buckets', 'min_probability', 'cost_per_contact', 'max_contacts']
  .map(x => ({ accessorKey: x, header: x }))
const aCols = ['rank', 'user_id', 'probability', 'segment', 'rfm_bucket', 'monetary', 'score', 'why'].map(x => ({ accessorKey: x, header: x }))
const kCols = ['mode', 'size', 'expected_conversions', 'expected_profit', 'avg_probability'].map(x => ({ accessorKey: x, header: x }))
const audRows = computed(() => (aud.value?.audience || []).map((a: any) => ({ ...a, why: (a.reasons || []).join('; ') })))
const cmpRows = computed(() => cmp.value?.metrics ? ['rule', 'ml'].map(m => ({ mode: m, ...cmp.value.metrics[m] })) : [])
async function loadAudience() {
  aud.value = await mlGet(`/campaigns/${cid.value}/recommended-audience?mode=${mode.value}&limit=10`)
  cmp.value = await mlGet(`/campaigns/${cid.value}/targeting-comparison`)
}
onMounted(async () => {
  const c = await mlGet<any[]>('/campaigns')
  if (!c) { down.value = true; return }
  campaigns.value = c.map(x => ({ ...x, target_segments: (x.target_segments || []).join(', '), eligible_buckets: (x.eligible_buckets || []).join(', ') }))
})
</script>
