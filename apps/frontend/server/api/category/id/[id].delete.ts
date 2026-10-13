import { eq } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { category } from "~~/server/database/schemas/category.schema";

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  if (!id){
    return "Error"
  }

  const result = await db.delete(category).where(eq(category.category_id, Number(id)))

  return result[0].affectedRows == 1;
})
