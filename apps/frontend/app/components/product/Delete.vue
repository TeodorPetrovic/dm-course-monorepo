<template>
  <UModal :open="open" :title="`Deleting product ${props.productId}`" :close="{ onClick: () => emit('close', false) }"
    description="You are deleting the product">

    <template #footer>
      <p v-bind="error" class="text-red-600"></p>
      <UButton @click="onSubmit">Delete</UButton>
    </template>
  </UModal>
</template>

<script lang="ts" setup>

const error = ref();
defineShortcuts({
  escape: () => emit('close', false)
})

const emit = defineEmits<{ close: [boolean] }>()

const props = defineProps<{
  productId: number
  open: boolean
}>();

async function onSubmit() {
  await $fetch("/api/product/id/" + props.productId, {
    method: "DELETE",
  }).then((res) => {
    if (res) {
      emit('close', true)
    } else {
      error.value = "Something went wrong"
    }
  }).catch((error) => {
    error.value = "Something went wrong"
  })
}

</script>