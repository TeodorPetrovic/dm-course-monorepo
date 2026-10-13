<template>
  <div class="w-full">
    <UDashboardNavbar title="Products">
      <template #leading>
        <UDashboardSidebarCollapse />
      </template>
      <template #right>
        <UButton icon="i-lucide-plus" to="/admin/product/create">Create Product</UButton>
      </template>
    </UDashboardNavbar>
    <div class="p-5 pt-0 flex flex-col flex-1 w-full">
      <div class="flex py-3.5">
        <UInput v-model="globalFilter" class="max-w-sm" placeholder="Filter name..." />
      </div>

      <UTable ref="table" :data="products" v-model:pagination="pagination" v-model:global-filter="globalFilter"
        :columns="columns" :pagination-options="{
          getPaginationRowModel: getPaginationRowModel()
        }" class="flex-1" :ui="{
          base: 'table-fixed border-separate border-spacing-0',
          thead: '[&>tr]:bg-elevated/50 [&>tr]:after:content-none',
          tbody: '[&>tr]:last:[&>td]:border-b-0',
          th: 'py-2 first:rounded-l-lg last:rounded-r-lg border-y border-default first:border-l last:border-r',
          td: 'border-b border-default',
          separator: 'h-0'
        }" />
      <div class="flex justify-center border-t border-default pt-4">
        <UPagination :default-page="(table?.tableApi?.getState().pagination.pageIndex || 0) + 1"
          :items-per-page="table?.tableApi?.getState().pagination.pageSize"
          :total="table?.tableApi?.getFilteredRowModel().rows.length"
          @update:page="(p) => table?.tableApi?.setPageIndex(p - 1)" />
      </div>
    </div>
    <ProductDelete :product-id="selectedProductId" :open="deleteDialogShow" @close="toggleDeleteDialog" />
  </div>
</template>

<script lang="ts" setup>
import type { TableColumn } from '@nuxt/ui';
import { getPaginationRowModel, type Row } from '@tanstack/vue-table'
import { useClipboard } from '@vueuse/core'
import type { Product } from '~/types/Product';

const UButton = resolveComponent('UButton')
const UDropdownMenu = resolveComponent('UDropdownMenu')

definePageMeta({
  layout: 'admin'
})

const toast = useToast()
const { copy } = useClipboard()
const table = useTemplateRef('table')
const deleteDialogShow = ref(false);
const selectedProductId = ref(0);
const products: Product[] = await $fetch("/api/shop");

async function toggleDeleteDialog(refresh: boolean) {
  deleteDialogShow.value = !deleteDialogShow.value
  if (refresh) {
    // TODO: Implement refresh on toggleDeleteDialog
    // categories = await $fetch("/api/category");
  }
}

const pagination = ref({
  pageIndex: 0,
  pageSize: 5
})

const globalFilter = ref('')

const columns: TableColumn<Product>[] = [
  {
    accessorKey: 'product_id',
    header: '#',
    cell: ({ row }) => `#${row.getValue('product_id')}`
  },
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => row.getValue('name')
  },
  {
    accessorKey: 'slug',
    header: 'Slug',
    cell: ({ row }) => row.getValue('slug')
  },
  {
    accessorKey: 'desc',
    header: 'Description',
    cell: ({ row }) => row.original.description.substring(0, 20)
  },
  {
    accessorKey: 'created_at',
    header: 'Created at',
    cell: ({ row }) => {
      return new Date(row.getValue('created_at')).toLocaleString('en-US', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }
  },
  {
    accessorKey: 'updated_at',
    header: 'Updated at',
    cell: ({ row }) => {
      return new Date(row.getValue('updated_at')).toLocaleString('en-US', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      return h(
        'div',
        { class: 'text-right' },
        h(
          UDropdownMenu,
          {
            content: {
              align: 'end'
            },
            items: getRowItems(row),
            'aria-label': 'Actions dropdown'
          },
          () =>
            h(UButton, {
              icon: 'i-lucide-ellipsis-vertical',
              color: 'neutral',
              variant: 'ghost',
              class: 'ml-auto',
              'aria-label': 'Actions dropdown'
            })
        )
      )
    }
  }
]

function getRowItems(row: Row<Product>) {
  return [
    {
      type: 'label',
      label: 'Actions'
    },
    {
      label: 'Edit',
      onSelect() {
        navigateTo('/admin/product/update/' + row.original.product_id)
      }
    },
    {
      label: 'Delete',
      color: 'warning',
      onSelect() {
        selectedProductId.value = row.original.product_id;
        toggleDeleteDialog(false)
      }
    },
  ]
}
</script>