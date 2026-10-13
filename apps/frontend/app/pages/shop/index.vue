<!-- Day 8: shop grid sa Default / Personalized poretkom (hybrid preporuke za demo korisnika). -->
<template>
  <div>
    <div class="flex items-center justify-center gap-4 py-5">
      <h1 class="text-2xl font-bold">Shop</h1>
      <UButtonGroup>
        <UButton :variant="mode === 'default' ? 'solid' : 'outline'" @click="mode = 'default'">Default</UButton>
        <UButton :variant="mode === 'personalized' ? 'solid' : 'outline'" :disabled="!recIds.length"
          @click="mode = 'personalized'" data-testid="personalized-toggle">Personalized</UButton>
      </UButtonGroup>
      <UInput v-model.number="userId" type="number" class="w-28" @change="loadRecs" />
      <span class="text-sm text-muted" data-testid="shop-status">
        <template v-if="recIds.length">user {{ userId }} · {{ recIds.length }} preporučenih · pomereno {{ moved }}</template>
        <template v-else>{{ recNote }}</template>
      </span>
    </div>
    <div class="p-10 pt-0 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <UCard v-for="product in ordered" :key="product.product_id">
        <template #header>
          <UBadge v-if="mode === 'personalized' && recIds.includes(product.product_id)" color="primary">For you</UBadge>
          <UBadge v-else variant="subtle">Sale</UBadge>
        </template>
        <NuxtLink :to="`/product/${product.slug}`">
          <NuxtImg class="mx-auto w-full" :src="product.img_url" />
          <p class="text-lg font-bold pt-4">{{ product.name }}</p>
          <p class="text-gray-600 text-sm">{{ product.description.substring(0, 40) }}</p>
        </NuxtLink>
        <template #footer>
          <div class="flex items-center justify-between">
            <p class="text-xl font-bold">{{ formatPrice(product.price) }}</p>
            <UButton class="cursor-pointer" icon="i-lucide-shopping-cart" @click="addToShoppingCart(product)" />
          </div>
        </template>
      </UCard>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Product } from '~/types/Product';

const toast = useToast()
const products: Product[] = await $fetch("/api/shop");
const mode = ref<'default' | 'personalized'>('default')
const userId = ref(DEMO_USER_ID)
const recIds = ref<number[]>([])
const recNote = ref("personalizacija se učitava…")

async function loadRecs() {
  setDemoUserId(userId.value)
  const r = await mlGet<any>(`/recommendations/${userId.value}?limit=10`)
  if (!r) { recIds.value = []; recNote.value = "dm-ml nedostupan — default poredak"; mode.value = 'default'; return }
  recIds.value = (r.recommendations || []).map((x: any) => x.product_id)
  if (r.fallback) recNote.value = `fallback: ${r.fallback_reason}`
  recIds.value.forEach((id, i) => trackRecommendationImpression(id, "hybrid", i + 1))
}
onMounted(async () => { userId.value = getDemoUserId(); await loadRecs() })

const ordered = computed(() => {
  if (mode.value === 'default' || !recIds.value.length) return products
  const pos = new Map(recIds.value.map((id, i) => [id, i]))
  const rec = products.filter(p => pos.has(p.product_id)).sort((a, b) => pos.get(a.product_id)! - pos.get(b.product_id)!)
  return [...rec, ...products.filter(p => !pos.has(p.product_id))]
})
const moved = computed(() => ordered.value.filter((p, i) => products[i]?.product_id !== p.product_id).length)

async function addToShoppingCart(p: Product) {
  const ev = { product_id: p.product_id, price: p.price, category_id: p.category_id }
  await trackProductView(ev, "shop")
  if (await addToShoppingCartEvent(ev, 1, "shop")) toast.add({ title: 'Added to shopping cart', description: p.name })
}
</script>
