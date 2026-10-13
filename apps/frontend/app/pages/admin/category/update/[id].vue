<template>
  <div class="w-full">
    <UDashboardNavbar title="Update Category">
      <template #leading>
        <UDashboardSidebarCollapse />
      </template>
    </UDashboardNavbar>
    <div class="p-5 flex flex-col flex-1 w-full">
      <div class="pb-5">
        <UButton icon="i-lucide-arrow-left-to-line" class="cursor-pointer" @click="router.back" />
      </div>
      <UCard class="w-full md:w-1/2 self-center">
        <template #header>
          <h1> Updating category {{ data.category_id }}</h1>
        </template>
        <UForm ref="form" :schema="schema" :state="state" class="space-y-4 w-full" @submit="onSubmit">
          <UFormField label="Name" name="name">
            <UInput v-model="state.name" class="w-full" />
          </UFormField>

          <UFormField label="Slug" name="slug">
            <UInput v-model="state.slug" class="w-full" />
          </UFormField>
          
          <UFormField label="Image Url" name="img_url">
            <UInput v-model="state.img_url" class="w-full" />
          </UFormField>

          <div class="flex justify-end">
            <UButton type="submit" class="cursor-pointer">Update</UButton>
          </div>
        </UForm>
      </UCard>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { FormSubmitEvent } from '@nuxt/ui'
import z from 'zod'

definePageMeta({
  layout: 'admin'
})

const router = useRouter()
const route = useRoute();
const id = route.params.id;
const form = useTemplateRef('form')

const { data } = await useFetch('/api/category/id/' + id)

const schema = z.object({
  name: z.string('Name is required').min(3, 'Must be at least 3 characters').max(64, 'Must be at most 64 characters'),
  slug: z.string('Slug is required').regex(/^[a-z0-9\-]{3,128}$/, "You slug has to contain only lowercase letters, numbers and a - symbol"),
  img_url: z.httpUrl('Image Link is required'),
})
type Schema = z.output<typeof schema>
const state = reactive<Partial<Schema>>({
  name: data.value.name,
  slug: data.value.slug,
  img_url: data.value.img_url
})

async function onSubmit(event: FormSubmitEvent<Schema>) {
  await $fetch("/api/category/update/" + id, {
    method: "POST",
    body: event.data,
  }).then((res) => {
    if (res) {
      navigateTo('/admin/category')
    }
  }).catch((error) => {
    // Finish the create statement
    console.log(JSON.stringify(error.data, null, 2))
    form.value?.setErrors([
      {
        message: error.data.data.message,
        name: error.data.data.field
      }
    ])
  })
}
</script>