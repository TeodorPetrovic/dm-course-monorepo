<template>
  <div>
    <h1 class="text-center pt-10 text-2xl font-bold">Category</h1>
    <div class="p-10 grid grid-cols-3 gap-2">
      <UBlogPost
        v-for="category in categories"
        :image="category.img_url"
        class="w-full text-center"
        :title="category.name"
        :to="`/category/${category.slug}`"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>

const categories = await $fetch("/api/category");

</script>