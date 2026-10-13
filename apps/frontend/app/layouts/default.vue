<template>
  <UHeader title="DM">
    <UNavigationMenu :items="items" />

    <template #body>
      <UNavigationMenu :items="items" orientation="vertical" />
    </template>
  </UHeader>

  <main>
    <slot />
  </main>

  <UFooter>
    <p class="text-muted text-sm">Copyright © {{ new Date().getFullYear() }}</p>
  </UFooter>
</template>

<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const route = useRoute()
getOrGenerateSessionId()

const items = computed<NavigationMenuItem[]>(() => [
  {
    label: 'Home',
    to: '/',
    active: route.path == "/"
  },
  {
    label: 'Shop',
    to: '/shop',
    active: route.path.startsWith('/shop')
  },
  {
    label: 'Category',
    to: '/category',
    active: route.path.startsWith('/category')
  },
  {
    label: 'Admin',
    to: '/admin',
  },
])

</script>