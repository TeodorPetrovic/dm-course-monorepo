import { db } from "~~/server/database/connection";
import { category } from "~~/server/database/schemas/category.schema";

export default defineEventHandler(async (event) => {
  const categories = db.select().from(category);
  return categories;
})
