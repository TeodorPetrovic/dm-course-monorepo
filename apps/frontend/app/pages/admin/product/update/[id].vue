<template>
  <div class="w-full">
    <UDashboardNavbar title="Update Product">
      <template #leading>
        <UDashboardSidebarCollapse />
      </template>
    </UDashboardNavbar>
    <div class="p-5 flex flex-1 w-full overflow-auto h-[90%]">
      <div class="pb-5">
        <UButton icon="i-lucide-arrow-left-to-line" class="cursor-pointer" @click="router.back" />
      </div>
      <UCard class="w-full md:w-1/2 mt-60 self-center mx-auto">
        <template #header>
          <h1> Updating product {{ data.product_id }}</h1>
        </template>
        <UForm ref="form" :schema="schema" :state="state" class="space-y-4 w-full" @submit="onSubmit">
          <UFormField label="Name" name="name">
            <UInput v-model="state.name" class="w-full" />
          </UFormField>

          <UFormField label="Slug" name="slug">
            <UInput v-model="state.slug" class="w-full" />
          </UFormField>

          <UFormField>
            <USelect placeholder="Select a category" v-model="state.category_id" :items="categories" class="w-1/2"/>
          </UFormField>
          
          <UFormField label="Description" name="description">
            <UTextarea v-model="state.description" class="w-full" />
          </UFormField>
          
          <UFormField label="Image Url" name="img_url">
            <UInput v-model="state.img_url" class="w-full" />
          </UFormField>

          <USeparator/>

          <h1 class="text-lg font-bold"> Seo Options</h1>
          <UFormField label="Seo Title" name="seo_title">
            <UInput v-model="state.seo_title" class="w-full" />
          </UFormField>

          <UFormField label="Seo Description" name="seo_description">
            <UInput v-model="state.seo_description" class="w-full" />
          </UFormField>
          
          <UFormField label="Seo Keywords" name="seo_keywords">
            <UInputTags v-model="state.seo_keywords" placeholder="Enter tags..." class="w-full"/>
          </UFormField>

          <div class="flex justify-end gap-5">
            <UButton @click="generateSeo" class="cursor-pointer">Generate</UButton>
            <UButton type="submit" class="cursor-pointer">Update</UButton>
          </div>
        </UForm>
      </UCard>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { FormSubmitEvent, SelectItem } from '@nuxt/ui'
import z from 'zod'

definePageMeta({
  layout: 'admin'
})

const router = useRouter()
const route = useRoute();
const id = route.params.id;
const form = useTemplateRef('form')

const { data } = await useFetch('/api/product/id/' + id)
const categoriesData = await $fetch("/api/category");
console.log(data)
console.log(categoriesData)

const categories = ref<SelectItem[]>(
  categoriesData.map(cat => {
    return {
      label: cat.name,
      value: cat.category_id
    }
  })
)

const schema = z.object({
  name: z.string('Name is required').min(3, 'Must be at least 3 characters').max(64, 'Must be at most 64 characters'),
  slug: z.string('Slug is required').regex(/^[a-z0-9\-]{3,128}$/, "You slug has to contain only lowercase letters, numbers and a - symbol"),
  category_id: z.int('Categori required'),
  description: z.string('Description is required'),
  seo_id: z.int(),
  img_url: z.httpUrl('Image Link is required'),
  seo_title: z.string('Title is required').min(3, 'Must be at least 3 characters').max(60, 'Must be at most 60 characters'),
  seo_description: z.string('Description is required').max(155, 'Must be at most 155 characters'),
  seo_keywords: z.array(z.string())
})
type Schema = z.output<typeof schema>
const state = reactive<Partial<Schema>>({
  name: data.value.name,
  slug: data.value.slug,
  seo_id: data.value.seo_id,
  category_id: data.value.category_id,
  description: data.value.description,
  img_url: data.value.img_url,
  seo_title: data.value.seo.title,
  seo_description: data.value.seo.description,
  seo_keywords: data.value.seo.key_words
})

async function onSubmit(event: FormSubmitEvent<Schema>) {
  console.log("test")
  await $fetch("/api/product/update/" + id, {
    method: "POST",
    body: event.data,
  }).then((res) => {
    if (res) {
      navigateTo('/admin/product')
    }
  }).catch((error) => {
    form.value?.setErrors([
      {
        message: error.data.data.message,
        name: error.data.data.field
      }
    ])
  })
}

export interface SeoResponse {
  title: string
  description: string
  keywords: string[]
}

async function generateSeo() {

  const data = {
    title: state.name,
    description: state.description,
  }

  await $fetch("/ml/seo/generate/product", {
    method: "POST",
    body: data
  }).then((res: any) => {
    const result: SeoResponse = res
    state.seo_title = result.title
    state.seo_description = result.description
    state.seo_keywords = result.keywords
  })
}
</script>