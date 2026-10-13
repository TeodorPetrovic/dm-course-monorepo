import { and, eq, ne } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { NewProduct, product } from "~~/server/database/schemas/product.schema";
import { seo } from "~~/server/database/schemas/seo.schema";

export interface UpdateProduct {
  name: string;
  description: string;
  img_url: string;
  slug: string;
  seo_id: number;
  category_id: number;
  seo_title: string,
  seo_description: string,
  seo_keywords: string[]
}

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, "id");
  const data: UpdateProduct = await readBody(event);

  // Check if ther does exist an slug with this name
  const exists = await db.select().from(product).where(
    and(
      eq(product.slug, data.slug),
      ne(product.product_id, Number(id))
    )
  )

  if (exists.length > 0) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      data: {
        field: "slug",
        message: "Slug is taken"
      }
    })
  }

  const productResult = await db.update(product)
    .set({
      name: data.name,
      slug: data.slug,
      description: data.description,
      seo_id: data.seo_id,
      img_url: data.img_url,
      updated_at: new Date()
    })
    .where(eq(product.product_id, Number(id)))

  const seoResult = await db.update(seo)
    .set({
      title: data.seo_title,
      description: data.seo_description,
      key_words: data.seo_keywords
    })
    .where(eq(seo.seo_id, Number(data.seo_id)))

  return productResult[0].affectedRows == 1 && seoResult[0].affectedRows
})
