<template>
  <div>
    <div class="px-10 flex items-center">
      <UButton icon="i-lucide-arrow-left-to-line" @click="router.back" />
      <h1 class="text-center text-2xl font-bold py-4 mx-auto">{{ data.category.name }}</h1>
    </div>
    <div class="p-10 pt-0 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <UCard v-for="product in data.products" :key="product.product_id">
        <NuxtLink :to="`/product/${product.slug}`">
          <NuxtImg class="mx-auto w-full" :src="product.img_url" />
          <p class="text-lg font-bold pt-4">{{ product.name }}</p>
          <p class="text-gray-600 text-sm">{{ product.description.substring(0, 60) }}</p>
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
import type { Category } from '~/types/Category';
import type { Product } from '~/types/Product';

const router = useRouter()
const route = useRoute()
const toast = useToast()
const slug = route.params.slug;

interface CategoryData { category: Category, products: Product[] }
const data: CategoryData = await $fetch("/api/category/" + slug);

onMounted(() => trackCategoryView(data.category.category_id))

async function addToShoppingCart(p: Product) {
  // korisnik je proizvod "video" na kategorijskoj strani -> product_view (source=category_page) + add_to_cart
  const ev = { product_id: p.product_id, price: p.price, category_id: p.category_id }
  await trackProductView(ev, "category_page")
  if (await addToShoppingCartEvent(ev, 1, "category_page")) toast.add({ title: 'Added to shopping cart', description: p.name })
}
</script>
