import { asc, eq } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { category } from "~~/server/database/schemas/category.schema";
import { product } from "~~/server/database/schemas/product.schema";

export default defineEventHandler(async (event) => {
  const slug = getRouterParam(event, "slug");
  if (!slug) throw createError({ statusCode: 400, statusMessage: 'No slug given' })
  const cat = await db.select().from(category).where(eq(category.slug, slug));
  if (!cat.length) throw createError({ statusCode: 404, statusMessage: 'Category not found' })
  const allProducts = await db.select().from(product).where(eq(product.category_id, cat[0].category_id))
    .orderBy(asc(product.product_id))
  return { category: cat[0], products: allProducts };
})
