import { eq } from "drizzle-orm";
import { product } from "~~/server/database/schemas/product.schema";

export default defineEventHandler(async (event) => {
  const slug = getRouterParam(event, 'slug');
  if (!slug) throw createError({ statusCode: 400, statusMessage: "No slug given" })
  const prod = await productWithSeo(eq(product.slug, slug))
  if (!prod) throw createError({ statusCode: 404, statusMessage: "Product not found" })
  return prod;
})
