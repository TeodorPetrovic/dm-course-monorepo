// Pozivi dm-ml kroz Nitro proxy /ml/** -> :3001. Graceful fallback: greška -> null (stranica se ne ruši).
import type { Product, Rec } from '~/types/Product'

export async function mlGet<T = any>(path: string): Promise<T | null> {
    try {
        return await $fetch<T>("/ml" + path)
    } catch (e) {
        console.warn("dm-ml unavailable:", path, e)
        return null
    }
}

export async function mlPost<T = any>(path: string, body: unknown = {}): Promise<{ data: T | null, error: string | null }> {
    try {
        return { data: await $fetch<T>("/ml" + path, { method: "POST", body }), error: null }
    } catch (e: any) {
        return { data: null, error: e?.data?.detail ? JSON.stringify(e.data.detail) : String(e?.message || e) }
    }
}

// Katalog iz lokalne baze (slug, slika, cena) — dopunjava preporuke koje vraćaju samo product_id/name.
const catalog = ref<Record<number, Product>>({})
export async function useCatalog() {
    if (!Object.keys(catalog.value).length) {
        try {
            const rows = await $fetch<Product[]>("/api/shop")
            catalog.value = Object.fromEntries(rows.map(p => [p.product_id, p]))
        } catch { /* bez kataloga: preporuke se prikazuju samo sa imenom */ }
    }
    return catalog
}

export function enrich(recs: Rec[] | undefined, cat: Record<number, Product>): Rec[] {
    return (recs || []).map(r => ({ ...cat[r.product_id], ...r, slug: r.slug || cat[r.product_id]?.slug,
        img_url: r.img_url || cat[r.product_id]?.img_url, price: r.price ?? cat[r.product_id]?.price ?? null }))
}

export function formatPrice(p: number | null | undefined) {
    return p == null ? "—" : `€${Number(p).toFixed(2)}`
}
