import { desc, eq, sql } from "drizzle-orm";
import { db } from "~~/server/database/connection";
import { event } from "~~/server/database/schemas/event.schema";

// Admin: poslednji događaji + brojanje po tipu (provera da tracking radi).
export default defineEventHandler(async (h) => {
    const q = getQuery(h)
    const limit = Math.min(Number(q.limit || 50), 500)
    const where = q.session ? eq(event.user_session, String(q.session)) : undefined
    const rows = await db.select().from(event).where(where).orderBy(desc(event.event_id)).limit(limit)
    const counts = await db.select({ event_type: event.event_type, n: sql<number>`count(*)` }).from(event)
        .where(where).groupBy(event.event_type)
    return { events: rows, counts }
})
