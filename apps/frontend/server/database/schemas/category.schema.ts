import { int, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

export const category = mysqlTable("category", {
    category_id: int("category_id").primaryKey().autoincrement(),
    name: varchar("name", { length: 255}).notNull(),
    slug: varchar("slug", { length: 255}).notNull(),
    img_url: text("img_url").notNull(),
    created_at: timestamp("created_at").notNull().defaultNow(),
    updated_at: timestamp("updated_at").notNull().defaultNow().onUpdateNow(),
})

export type Category = typeof category.$inferSelect
export type NewCategory = typeof category.$inferInsert