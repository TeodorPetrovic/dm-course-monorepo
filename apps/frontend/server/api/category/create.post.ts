import { eq } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { category, NewCategory } from "~~/server/database/schemas/category.schema";

export default defineEventHandler(async (event) => {
  const data: NewCategory = await readBody(event);

  // Check if ther does exist an slug with this name
  const exists = await db.select().from(category).where(eq(category.slug, data.slug))

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

  // TODO: Fix updated and created At in the schema
  data.created_at = new Date();
  data.updated_at = new Date();
  const result = await db.insert(category).values(data);
  if (!result[0].insertId) {
    return false
  }

  return true
})
