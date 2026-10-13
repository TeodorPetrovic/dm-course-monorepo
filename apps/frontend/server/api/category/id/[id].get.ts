import { eq } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { category } from "~~/server/database/schemas/category.schema";

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  if (!id){
    return "Error"
  }

  const cat = await db.select().from(category).where(eq(category.category_id, Number(id)));

  return cat[0];
})
