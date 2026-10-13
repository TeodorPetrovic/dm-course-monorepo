// Server-side poziv dm-ml API-ja (best-effort). ML_API_URL podrazumevano http://127.0.0.1:3001.
export const ML_API_URL = process.env.ML_API_URL || "http://127.0.0.1:3001"

export async function forwardToMl(path: string, body: unknown): Promise<{ ok: boolean, status?: number, error?: string }> {
    try {
        const r = await fetch(ML_API_URL + path, {
            method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
            signal: AbortSignal.timeout(3000),
        })
        return { ok: r.ok, status: r.status }
    } catch (e: any) {
        return { ok: false, error: String(e?.message || e) }
    }
}
