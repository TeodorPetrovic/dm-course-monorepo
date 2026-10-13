<template>
  <div class="px-10 pt-4">
    <UButton icon="i-lucide-arrow-left-to-line" @click="router.back" />
  </div>
  <div class="grid grid-cols-3 gap-6 px-20 pt-5">
    <div class="col-span-2 h-full">
      <NuxtImg class="mx-auto w-1/2 border" :src="data.img_url" />
      <p class="pt-5">{{ data.description }}</p>

      <!-- Day 12: Platform sekcija (AI opis sa fallback-om + module_class) -->
      <UCard v-if="platform" class="mt-6" data-testid="platform-section">
        <p class="text-sm text-muted">Platform · {{ platform.ai_description?.source }}
          <span v-if="platform.ai_description?.fallback">(fallback: {{ platform.ai_description?.fallback_reason }})</span></p>
        <p>{{ platform.ai_description?.content }}</p>
      </UCard>

      <RecSection title="Recommended Products" source="content" :items="content" :fallback="contentFallback" />
      <RecSection title="Customers Also Viewed" source="collaborative" :items="collab" :fallback="collabFallback" />
      <RecSection title="Based on your session" source="session" :items="session" :fallback="sessionFallback"
        :note="sessionFallback ? 'nema dovoljno signala u sesiji' : ''" />
      <RecSection title="Semantically similar" source="semantic" :items="semantic" />
    </div>
    <div class="relative">
      <div class="sticky top-4 px-5 py-5 border-2 rounded-lg w-[300px]">
        <UBadge color="error">Sale</UBadge>
        <p class="text-2xl font-bold pt-4" data-testid="product-name">{{ data.name }}</p>
        <p class="text-gray-600">{{ data.description }}</p>
        <p class="text-2xl pb-2 font-bold" data-testid="product-price">{{ formatPrice(data.price) }}</p>
        <UButton @click="addToCart" class="w-full mb-2 cursor-pointer">Add to cart</UButton>
        <UButton v-if="inCart" @click="removeFromCart" variant="ghost" class="w-full mb-2 cursor-pointer">Remove from cart</UButton>
        <UButton @click="buy" variant="outline" class="w-full cursor-pointer">Buy</UButton>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Product, Rec } from '~/types/Product';

const router = useRouter()
const route = useRoute()
const toast = useToast()
const slug = route.params.slug;

const data: Product = await $fetch("/api/product/" + slug)
if (!data) throw createError({ statusCode: 404, statusMessage: "Product not found" })

const content = ref<Rec[]>([]); const contentFallback = ref(false)
const collab = ref<Rec[]>([]); const collabFallback = ref(false)
const session = ref<Rec[]>([]); const sessionFallback = ref(false)
const semantic = ref<Rec[]>([])
const platform = ref<any>(null)
const inCart = ref(false)
const P = () => ({ product_id: data.product_id, price: data.price, category_id: data.category_id })

onMounted(async () => {
  const src = (history.state?.back || "").startsWith("/category") ? "category_page"
            : (history.state?.back || "").startsWith("/shop") ? "shop"
            : (history.state?.back || "").startsWith("/search") ? "search_page" : "product_page"
  await trackProductView(P(), src)
  const cat = (await useCatalog()).value
  // svaka sekcija je nezavisna: ako jedan modul padne, ostale se i dalje prikazuju
  await Promise.all([loadContent(cat), loadCollab(cat), loadSession(cat), loadSemantic(cat), loadPlatform()])
})

async function loadContent(cat: Record<number, Product>) {
  // TEACH d05: content-based preporuke (TF-IDF)
  const c = await mlGet<any>(`/recommendations/content/${data.product_id}?limit=5`)
  if (c) { content.value = enrich(c.recommendations, cat); contentFallback.value = !!c.fallback }
  // /TEACH
}
async function loadCollab(cat: Record<number, Product>) {
  // TEACH d06: collaborative preporuke (item-item)
  const cf = await mlGet<any>(`/recommendations/collaborative/${data.product_id}?limit=5`)
  if (cf) { collab.value = enrich(cf.recommendations, cat); collabFallback.value = !!cf.fallback }
  // /TEACH
}
async function loadSession(cat: Record<number, Product>) {
  // TEACH d09: preporuke na osnovu tekuće sesije
  const se = await mlGet<any>(`/recommendations/session/${getOrGenerateSessionId()}?limit=5`)
  if (se) { session.value = enrich(se.recommendations, cat); sessionFallback.value = !!se.fallback }
  // /TEACH
}
async function loadSemantic(cat: Record<number, Product>) {
  // TEACH d10: semantički slični proizvodi (embeddings)
  const sm = await mlGet<any>(`/recommendations/semantic/${data.product_id}?limit=5`)
  if (sm) semantic.value = enrich(sm.recommendations, cat)
  // /TEACH
}
async function loadPlatform() {
  // TEACH d12: platform payload (AI opis + module_class)
  platform.value = await mlGet<any>(`/platform/product/${data.product_id}`)
  // /TEACH
}

useSeoMeta({
  title: data.seo?.title,
  ogTitle: data.seo?.title,
  description: data.seo?.description,
  ogDescription: data.seo?.description,
  ogImage: data.img_url,
  ogUrl: 'http://localhost:3000/product/' + slug,
  twitterCard: 'summary_large_image',
})
useHead({ htmlAttrs: { lang: 'en' }, meta: [{ name: 'keywords', content: (data.seo?.key_words || []).join(", ") }] })

async function addToCart() {
  if (await addToShoppingCartEvent(P())) {
    inCart.value = true
    toast.add({ title: 'Added to shopping cart', description: data.name, icon: 'i-lucide-shopping-cart' })
  }
}
async function removeFromCart() {
  if (await removeFromCartEvent(P())) { inCart.value = false; toast.add({ title: 'Removed from cart', description: data.name }) }
}
async function buy() {
  if (await buyProductEvent(P())) {
    inCart.value = false
    toast.add({ title: 'Purchase recorded', description: data.name, icon: 'i-lucide-check' })
  }
}
</script>
