import { eq, type SQL } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { product } from "~~/server/database/schemas/product.schema";
import { seo } from "~~/server/database/schemas/seo.schema";

// Eksplicitan LEFT JOIN umesto db.query...with (relacioni upit koristi LATERAL JOIN koji MariaDB ne podržava;
// ovako radi i na MySQL 8 i na MariaDB).
export async function productWithSeo(where: SQL) {
    const rows = await db.select({ product, seo }).from(product).leftJoin(seo, eq(product.seo_id, seo.seo_id))
        .where(where).limit(1)
    if (!rows.length) return null
    const { product: p, seo: s } = rows[0]
    const kw = typeof s?.key_words === "string" ? JSON.parse(s.key_words) : s?.key_words
    return { ...p, seo: s ? { ...s, key_words: kw } : null }
}
