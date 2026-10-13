import { asc } from "drizzle-orm"
import { db } from "~~/server/database/connection"
import { product } from "~~/server/database/schemas/product.schema"

export default defineEventHandler(async () => {
  return db.select().from(product).orderBy(asc(product.product_id));
})
