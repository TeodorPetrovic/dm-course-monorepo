<!-- Day 3: model konverzije — trening, metrike + baseline, leakage before/after, predikcija po korisniku. -->
<template>
  <div class="p-6">
    <div class="flex items-center gap-4 mb-4">
      <h1 class="text-2xl font-bold">Conversion model</h1>
      <USelect v-model="modelType" :items="['logistic_regression', 'random_forest']" class="w-56" />
      <UButton :loading="busy" @click="train" data-testid="train-conversion">Treniraj</UButton>
    </div>
    <MlUnavailable v-if="down" />
    <UAlert v-else-if="!status" color="info" variant="subtle" title="Model nije treniran"
      description="Kliknite „Treniraj“ (POST /ml/models/conversion/train)." class="mb-4" data-testid="untrained" />
    <p v-if="err" class="text-error mb-2">{{ err }}</p>
    <template v-if="status">
      <p class="text-sm mb-2">{{ status.model_type }} · window {{ status.window_days }} d · cutoff {{ status.cutoff }} ·
        train {{ status.n_train }} / test {{ status.n_test }} · base rate {{ status.base_rate }}</p>
      <UTable :data="metricRows" :columns="mCols" class="mb-4" data-testid="metrics-table" />
      <p class="text-sm mb-4">Confusion matrix (model): {{ status.metrics.confusion_matrix }} · baseline: {{ status.baseline.confusion_matrix }}</p>
      <template v-if="leak">
        <h2 class="text-xl font-bold mb-2">Leakage: clean vs leaky</h2>
        <UTable :data="leakRows" :columns="mCols" class="mb-6" />
      </template>
    </template>
    <h2 class="text-xl font-bold mb-2">Predikcija po korisniku</h2>
    <div class="flex gap-2 items-center">
      <UInput v-model.number="uid" type="number" class="w-32" />
      <UButton @click="predict" data-testid="predict">GET probability</UButton>
      <span v-if="pred" data-testid="prediction">p = {{ pred.probability }}
        <UBadge v-if="pred.fallback" color="warning">fallback: {{ pred.reason }}</UBadge></span>
      <span v-if="predErr" class="text-error">{{ predErr }}</span>
    </div>
  </div>
</template>
<script lang="ts" setup>
definePageMeta({ layout: 'admin' })
const modelType = ref('logistic_regression'); const status = ref<any>(null); const leak = ref<any>(null)
const busy = ref(false); const err = ref(""); const down = ref(false)
const uid = ref(DEMO_USER_ID); const pred = ref<any>(null); const predErr = ref("")
const mCols = ['name', 'accuracy', 'precision', 'recall', 'f1'].map(x => ({ accessorKey: x, header: x }))
const metricRows = computed(() => status.value ? [{ name: 'model', ...status.value.metrics }, { name: 'majority baseline', ...status.value.baseline }] : [])
const leakRows = computed(() => leak.value ? [{ name: 'clean', ...leak.value.clean }, { name: 'leaky', ...leak.value.leaky }] : [])
async function load() {
  try { status.value = await $fetch('/ml/models/conversion/status'); down.value = false }
  catch (e: any) { status.value = null; down.value = !(e?.statusCode === 503 || e?.status === 503) }
}
async function train() {
  // TEACH d03: POST /models/conversion/train
  busy.value = true
  const r = await mlPost<any>('/models/conversion/train', { model_type: modelType.value })
  busy.value = false; err.value = r.error || ""
  if (r.data) { leak.value = r.data.leakage; await load() }
  // /TEACH
}
async function predict() {
  // TEACH d03: verovatnoća kupovine za korisnika
  pred.value = null; predErr.value = ""
  try { pred.value = await $fetch(`/ml/customers/${uid.value}/conversion-probability`) }
  catch (e: any) { predErr.value = e?.statusCode === 503 ? 'model nije treniran' : 'dm-ml nedostupan' }
  // /TEACH
}
onMounted(load)
</script>
