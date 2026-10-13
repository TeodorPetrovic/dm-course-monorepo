<template>
  <UModal :open="open" :title="`Deleting category ${props.categoryId}`" :close="{ onClick: () => emit('close', false) }"
    description="You are deleting category">
    <!-- <UButton label="Delete" color="warning" /> -->

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
  categoryId: number
  open: boolean
}>();

async function onSubmit() {
  await $fetch("/api/category/id/" + props.categoryId, {
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