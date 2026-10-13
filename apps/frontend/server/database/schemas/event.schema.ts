import { datetime, decimal, int, mysqlTable, timestamp, varchar } from "drizzle-orm/mysql-core";

// Day 1: proširena šema događaja (stara polja event_type / user_session / product_id ostaju).
export const EVENT_TYPES = [
    "product_view", "category_view", "search", "add_to_cart", "remove_from_cart",
    "purchase", "recommendation_impression", "recommendation_click",
] as const
export const PRODUCT_EVENT_TYPES = ["product_view", "add_to_cart", "remove_from_cart", "purchase",
    "recommendation_impression", "recommendation_click"] as const
export const DEFAULT_SOURCE: Record<string, string> = {
    product_view: "product_page", category_view: "category_page", search: "search_page",
    add_to_cart: "product_page", remove_from_cart: "cart", purchase: "cart",
    recommendation_impression: "recommendation", recommendation_click: "recommendation",
}

export const event = mysqlTable("event", {
    event_id: int("event_id").primaryKey().autoincrement(),
    event_type: varchar("event_type", { length: 50}).notNull(),
    user_id: int("user_id"),
    user_session: varchar("user_session", { length: 255}).notNull(),
    product_id: int("product_id"),
    category_id: int("category_id"),
    price: decimal("price", { precision: 10, scale: 2, mode: "number" }),
    quantity: int("quantity").notNull().default(1),
    source: varchar("source", { length: 32 }).notNull().default("product_page"),
    timestamp: datetime("timestamp", { mode: "string" }).notNull(),
    recommendation_source: varchar("recommendation_source", { length: 32 }),
    recommendation_position: int("recommendation_position"),
    created_at: timestamp("created_at").defaultNow(),
})

export type Event = typeof event.$inferSelect
export type NewEvent = typeof event.$inferInsert
