<template>
  <UAlert color="warning" variant="subtle" :title="title || 'dm-ml nije dostupan'"
    :description="description || 'Pokrenite: cd dm-ml && .venv/bin/uvicorn app.main:app --port 3001'" class="mb-4" />
</template>
<script lang="ts" setup>
defineProps<{ title?: string, description?: string }>()
</script>
