# Design write-up — Integrated AI Marketing Platform (Day 12)

> Popuni sve sekcije. Ovo je glavni predati dokument za rubric (posebno
> **Design quality** i **Honest interpretation**). Drži se činjenica — piši o
> *svom* sistemu, ne o idealnom.

## 1. Arhitektura (dijagram + moduli)

Nacrtaj dijagram toka podataka: `events → profile → preporuke → AI sadržaj → evaluacija`, sa svakim modulom i njegovim **inputom/outputom**.

```
[npr.]
Day 1 events ──► Day 2 segment ──┐
            └──► Day 3 p(buy) ───┼──► Day 4 targeting hint ──► profile
Day 1+5 ─────► Day 8 hybrid ─────┼──► preporuke
Day 1 ───────► Day 9 session ────┤
Day 10 ──────► embeddings ───────┘
Day 11 ──────► AI content ───────► hero / featured
Day 7/8/9 ───► evaluation ───────► CTR / P@K
```

## 2. Označi svaku komponentu (taksonomija)

Za svaki modul koji tvoj sistem koristi: **klasa + baseline**.

| Modul (id) | Klasa (rule/heuristika/statistika/ML/genAI) | Baseline (s čime se poredi) | Zadatak u sistemu |
| --- | --- | --- | --- |
| `rfm` | rule / heuristic | — | profil bucket |
| `kmeans_segmentation` | ML | manual RFM (pravilo) | segment korisnika |
| `conversion_model` | ML | majority-class (statistika) | p(buy) |
| `popularity` | statistical / heuristic | — | fallback baseline |
| `content_tfidf` | statistical | keyword (Day 10) | preporuke po tekstu |
| `collaborative` | statistical / heuristic | session co-occurrence | item-item |
| `hybrid` | rule / heuristic pipeline | svaki pojedinačni izvor (Day 8) | user preporuke |
| `session` | rule / heuristic | popularity | session preporuke |
| `embeddings` | ML | TF-IDF (Day 10) | semantic |
| `generative_ai` | generative AI | template tekst (Day 11) | AI sadržaj |

## 3. Odluke i trade-off-ovi

Za svaku veliku odluku: šta si izabrao, koje alternative si odbacio i zašto.

| Odluka | Izbor | Alternative | Zašto |
| --- | --- | --- | --- |
| Redosled orkestracije (profil pre preporuka?) | … | … | … |
| Koje module poziva home page (a koje product page) | … | … | … |
| Evaluacija: CTR summary na home page-u, pun report u admin-u | … | … | … |
| Gde živi fallback (servis? CMS?) | … | … | … |
| … | … | … | … |

## 4. Failure handling

Za svaki scenario iz brief-a: koji modul puca, kako sistem reaguje, koji je
fallback, i gde si to *dokazao* (endpoint/poziv).

| Scenario | Modul koji puca | Fallback + razlog | Dokaz |
| --- | --- | --- | --- |
| Nepoznat korisnik | segment, konverzija | `unsegmented`, `base_rate` | `curl /platform/profile/999999` |
| Sesija bez signala | session | popularity `no_session_signal` | nova sesija na home page-u |
| Netreniran model | segment/konverzija | `untrained_model` | obriši `app/models/`, pa pozovi |
| LLM down | generative\_ai | template `model_unavailable` | hero `source=template` |
| Proizvod bez embeddinga | embeddings | popularity `no_embedding` | `/recommendations/semantic/{nov}` |
| Nema events.csv | svi zavisni | `available=false` | `/platform/modules` |

## 5. Evaluacija (šta meriš i zašto)

* **Šta** meriš: CTR (Day 9), P@K/R@K/NDCG (Day 7), hybrid vs single-source
  (Day 8) — ili nešto svoje.
* **Na kom pitanju**: npr. „da li je session-aware bolji od popularity za
  početnu stranu?"
* **Ograničenja**: metrike su dataset-specific; težine merge-a su ručne; CTR
  razlika nije statistički potvrđen A/B rezultat.

## 6. Šta rezultat NE dokazuje (iskrena interpretacija — obavezno)

1. **Radni sistem ≠ poslovna vrednost.** Sistem radi end-to-end, ali metrike
   (CTR, P@K) su računate na sintetičkom datasetu — ne znači da bi iste odluke
   bile dobre na realnom saobraćaju.
2. **„Inteligencija" je kompozicija, ne model.** Svaka komponenta je
   pravilo/heuristika/statistika/ML/generative AI — i mora da se označi.
   Hybrid „pobeda" nad pojedinačnim izvorima nije dokaz da je težinski blend
   naučen; težine su ručne.
3. **AI sadržaj može biti fluentAN i netačan.** Template fallback nije dokaz
   da je LLM „najbolji" — on je fail-safe. Validacija proverava strukturu, ne
   istinitost.
4. **CTR razlika nije A/B rezultat.** Day 9 pravi *prikupljanje podataka* za
   eksperiment, ne značajnosni test.
5. *(dodaj svoju)* …

## 7. Šta bi sledeće unapredio

* Naučene merge težine (ranking model, npr. LambdaMART) umesto heuristike.
* Pravi A/B test sa statističkim zaključkom.
* Online evaluacija (CTR iz live događaja) umesto offline report-a.
* Personalizacija generativnog sadržaja sa više konteksta (ne samo segment).
