<template>
  <UDashboardGroup>
    <UDashboardSidebar collapsible resizable :ui="{ footer: 'border-t border-default' }">
      <template #header="{ collapsed }">
        <p v-if="!collapsed" class="text-2xl font-bold w-full shrink-0">DM</p>
        <UIcon v-else name="i-simple-icons-nuxtdotjs" class="size-5 text-primary mx-auto" />
      </template>
      <template #default="{ collapsed }">
        <UNavigationMenu :collapsed="collapsed" :items="items[0]" orientation="vertical" />
      </template>
    </UDashboardSidebar>
    <UDashboardPanel>
      <template #body><slot /></template>
    </UDashboardPanel>
  </UDashboardGroup>
</template>

<script lang="ts" setup>
import type { NavigationMenuItem } from '@nuxt/ui';
const route = useRoute()
const nav = (label: string, to: string, icon = 'i-lucide-inbox') =>
  ({ label, icon, to, active: to === '/admin' ? route.path === to : route.path.startsWith(to) })
const items = computed<NavigationMenuItem[][]>(() => [[
  { label: 'Frontend Page', icon: 'i-lucide-house', to: '/' },
  nav('Dashboard', '/admin', 'i-lucide-layout-dashboard'),
  nav('Categories', '/admin/category'),
  nav('Products', '/admin/product'),
  nav('Events', '/admin/event', 'i-lucide-activity'),
  nav('Segments', '/admin/segments', 'i-lucide-users'),
  nav('Conversion', '/admin/conversion', 'i-lucide-target'),
  nav('Campaigns', '/admin/campaigns', 'i-lucide-megaphone'),
  nav('Recommendations', '/admin/recommendations', 'i-lucide-chart-bar'),
  nav('AI content', '/admin/ai', 'i-lucide-sparkles'),
  nav('Marketing', '/admin/marketing', 'i-lucide-chart-pie'),
]])
</script>
