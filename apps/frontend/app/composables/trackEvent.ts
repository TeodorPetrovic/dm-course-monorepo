// Day 1: trackEvent(payload) + pomagači za svih 8 tipova događaja.
// Session ID i demo korisnik žive u localStorage (samo na klijentu).

export type EventType = "product_view" | "category_view" | "search" | "add_to_cart" | "remove_from_cart"
    | "purchase" | "recommendation_impression" | "recommendation_click"

export interface TrackPayload {
    event_type: EventType
    product_id?: number | null
    category_id?: number | null
    price?: number | null
    quantity?: number
    source?: string
    recommendation_source?: string | null
    recommendation_position?: number | null
}

export const DEMO_USER_ID = 395  // najaktivniji korisnik u seed-u (Day 8/12 demo)

export function getOrGenerateSessionId() {
    if (import.meta.client) {
        let sessionId = localStorage.getItem('user_session')
        if (!sessionId) {
            sessionId = `session_live_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
            localStorage.setItem("user_session", sessionId)
        }
        return sessionId;
    }
}

export function getDemoUserId(): number {
    if (import.meta.client) {
        const v = Number(localStorage.getItem('dm_user_id'))
        return Number.isInteger(v) && v > 0 ? v : DEMO_USER_ID
    }
    return DEMO_USER_ID
}

export function setDemoUserId(id: number) {
    if (import.meta.client) localStorage.setItem('dm_user_id', String(id))
}

export async function trackEvent(payload: TrackPayload) {
    // TEACH d01: trackEvent -> POST /api/event/track (nikad ne ruši stranicu)
    if (!import.meta.client) return null
    try {
        return await $fetch("/api/event/track", {
            method: "POST",
            body: { ...payload, user_id: getDemoUserId(), user_session: getOrGenerateSessionId() },
        })
    } catch (e) {
        console.warn("trackEvent failed", e)   // tracking nikad ne ruši stranicu
        return null
    }
    // /TEACH
}

type P = { product_id: number, price?: number | null, category_id?: number | null }
export const trackProductView = (p: P, source = "product_page") =>
    trackEvent({ event_type: "product_view", ...p, source })
export const trackCategoryView = (category_id: number) =>
    trackEvent({ event_type: "category_view", category_id, source: "category_page" })
export const trackSearchEvent = () => trackEvent({ event_type: "search", source: "search_page" })
export const addToShoppingCartEvent = (p: P, quantity = 1, source = "product_page") =>
    trackEvent({ event_type: "add_to_cart", ...p, quantity, source })
export const removeFromCartEvent = (p: P) => trackEvent({ event_type: "remove_from_cart", ...p, source: "cart" })
export const buyProductEvent = (p: P, quantity = 1) =>
    trackEvent({ event_type: "purchase", ...p, quantity, source: "cart" })
export const trackRecommendationImpression = (product_id: number, recommendation_source: string, position: number) =>
    trackEvent({ event_type: "recommendation_impression", product_id, recommendation_source,
                 recommendation_position: position, source: "recommendation" })
export const trackRecommendationClick = (product_id: number, recommendation_source: string, position: number) =>
    trackEvent({ event_type: "recommendation_click", product_id, recommendation_source,
                 recommendation_position: position, source: "recommendation" })
