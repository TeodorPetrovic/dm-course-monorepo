import { drizzle } from "drizzle-orm/mysql2";
import mysql from "mysql2/promise";
import * as productSchema from "../database/schemas/product.schema"
import * as seoSchema from "../database/schemas/seo.schema"
import * as eventSchema from "../database/schemas/event.schema"
import * as categorySchema from "../database/schemas/category.schema"

// Podrazumevano LOKALNA MariaDB iz db/ (start_local_db.sh, port 3307).
// Prava baza se NE koristi; DB_* promenljive mogu da preusmere na drugu lokalnu bazu.
const connection = mysql.createPool({
    host: process.env.DB_HOST || "127.0.0.1",
    port: Number(process.env.DB_PORT || 3307),
    user: process.env.DB_USER || "dm_local",
    password: process.env.DB_PASSWORD || "dm_local",
    database: process.env.DB_NAME || "dm_local",
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0,
    decimalNumbers: true,
})

export const db = drizzle(connection, {
    schema: {
        ...productSchema,
        ...seoSchema,
        ...eventSchema,
        ...categorySchema,
    },
    mode: "default"
});
