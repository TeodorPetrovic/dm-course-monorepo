import { int, json, mysqlTable, varchar } from "drizzle-orm/mysql-core";

export const seo = mysqlTable("seo", {
    seo_id: int("seo_id").primaryKey().autoincrement(),
    title: varchar("title", { length: 60}).notNull(),
    description: varchar("description", { length: 155}).notNull(),
    key_words: json("key_words").notNull(),
})

export type Seo = typeof seo.$inferSelect
export type NewSeo = typeof seo.$inferInsert
