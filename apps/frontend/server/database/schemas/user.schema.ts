import { int, mysqlTable, timestamp, varchar } from "drizzle-orm/mysql-core";

export const user = mysqlTable("user", {
    user_id: int("user_id").primaryKey().autoincrement(),
    username: varchar("username", { length: 255 }).notNull(),
    email: varchar("email", { length: 255 }).notNull(),
    password: varchar("password", { length: 255 }).notNull(),
    created_at: timestamp("created_at").defaultNow(),
    updated_at: timestamp("updated_at").defaultNow().onUpdateNow(),
})