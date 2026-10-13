import { eq } from "drizzle-orm";
import { product } from "~~/server/database/schemas/product.schema";

export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'));
  if (!Number.isInteger(id)) throw createError({ statusCode: 400, statusMessage: "Invalid id" })
  const prod = await productWithSeo(eq(product.product_id, id))
  if (!prod) throw createError({ statusCode: 404, statusMessage: "Product not found" })
  return prod;
})
