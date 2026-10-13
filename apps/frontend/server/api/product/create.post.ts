import { eq } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { NewProduct, product } from "~~/server/database/schemas/product.schema";
import { NewSeo, seo } from "~~/server/database/schemas/seo.schema";

export interface CreateProduct {
  name: string;
  description: string;
  img_url: string;
  slug: string;
  category_id: number;
  seo_title: string,
  seo_description: string,
  seo_keywords: string[]
}

export default defineEventHandler(async (event) => {
  const data: CreateProduct = await readBody(event);

  // Check if the slug does exist an with this name
  const exists = await db.select().from(product).where(eq(product.slug, data.slug))

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

  const seoData: NewSeo = {
    title: data.seo_title,
    description: data.seo_description,
    key_words: data.seo_keywords
  }
  const seoResult = await db.insert(seo).values(seoData);

  const productData: NewProduct = {
    name: data.name,
    category_id: data.category_id,
    description: data.description,
    img_url: data.img_url,
    slug: data.slug,
    seo_id: seoResult[0].insertId,
    created_at: new Date(),
    updated_at: new Date()
  }
  
  // TODO: Fix updated and created At in the schema
  const result = await db.insert(product).values(productData);
  if (!result[0].insertId) {
    return false
  }

  return true
})
