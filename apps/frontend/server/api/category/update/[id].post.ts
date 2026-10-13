import { and, eq, ne } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { category, NewCategory } from "~~/server/database/schemas/category.schema";

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, "id");
  const data: NewCategory = await readBody(event);

  // Check if ther does exist an slug with this name
  const exists = await db.select().from(category).where(
    and(
      eq(category.slug, data.slug),
      ne(category.category_id, Number(id))
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

  const result = await db.update(category)
    .set({
      name: data.name,
      slug: data.slug,
      img_url: data.img_url,
      updated_at: new Date()
    })
    .where(eq(category.category_id, Number(id)))
    
    return result[0].affectedRows == 1
})
