# Dan 11 — Structured Generative-AI Marketing Service

- lesson_id: 121
- sort_order: 0
- status: draft
- created: 2026-09-05 19:57:48.080 updated: 2026-09-05 20:00:30.580
- summary: „LLM može da napiše SEO naslov koji je gramatički savršen — i potpuno izmišljen." Do sada su sve komponente bile determinističke: pravila i heuristike (RFM bucketi Day 2, targeting Day 4, hibrid Day 8, sesija Day 9), statistika (popularity, TF-IDF, CF — Day 5/6) i ML modeli (K-Means Day 2, klasifikator Day 3, embeddings Day 10). Danas uvodimo generative AI: model generiše tekst — i zato prvi put moramo da definišemo strukturu izlaza, validiramo ga, ograničimo retry i predvidimo pad. Ovo je popravka anti-pattern-a iz current-materials/ (beskonačan retry, positional key mapping, nema validacije, model hard-code-ovan u app kodu). [subjects-import]


---

<!-- page_id 432 order 0 -->
## [Page] Materijal

# Dan 11 — Structured Generative-AI Marketing Service

> *„LLM može da napiše SEO naslov koji je gramatički savršen — i potpuno izmišljen."*
> Do sada su sve komponente bile **determinističke** (u inferenciji): pravila i heuristike
> (Day 2/4/8/9), statistika (Day 5/6) i ML modeli (Day 2/3/10). Danas uvodimo **generative
> AI**: model *generiše tekst* — i zato prvi put moramo da **definišemo strukturu
> izlaza, validiramo ga, ograničimo retry i predvidimo pad**. Ovo je popravka
> anti-pattern-a iz `current-materials/` (beskonačan retry, positional key mapping,
> nema validacije, model hard-code-ovan u app kodu).

## Šta gradimo

**Structured generative-AI servis** — `AIProvider` apstrakciju (lokalni TinyLlama
ili external HTTP API), Pydantic šeme (`SEOResponse`/`ContentResponse`),
validaciju (`validate_generated_output`), **bounded retry + fail-safe**
(`generate_with_retry`), i generaciju SEO meta, opisa proizvoda, prodajne kopije
kampanje i ključnih reči — izložene kroz `POST /ai/seo` i `POST /ai/content` i
integrisane u CMS admin (Generate dugmad).

Day 5 je napravio tekstualni korpus proizvoda (`product_text` = kategorija + naziv +
opis) za TF-IDF; Day 11 uvodi template tekst (`app.services.templates`) i njegov **generativni
kontrast**: template je pravilo (baseline), LLM je model koji *može da pogreši*.
Zato je evaluacija dana **template-vs-LLM** (`Day 11/data/comparison.csv`) — iste
provere (dužina, obavezna polja, product facts) na obe strane.

Klasa komponenti (obavezno svake AI/ML komponente):

| Komponenta | Klasa |
| --- | --- |
| `SEOResponse` / `ContentResponse` | **data structure** (Pydantic šema izlaza) |
| `AIProvider` | **abstraction** (interfejs: `generate(prompt) -> str`) |
| `LocalModelProvider` | **generative AI** (transformers pipeline, npr. TinyLlama) |
| `ExternalProvider` | **generative AI** (OpenAI-compatible HTTP API) |
| `parse_json_output` / `validate_*` | **data validation** (struktura, dužine, facts) |
| `generate_with_retry` | **control flow** (bounded retry + fail-safe) |
| `template_seo_metadata` / `template_*` (`app.services.templates`) | **rule / heuristic** (baseline, bez LLM-a) |

## Application requirement

CMS admin produkt form (create/update) ima **Generate dugme** koje poziva
`POST /ai/seo` (`/ml/ai/seo` kroz Nitro proxy) i puni `seo_title`/
`seo_description`/`keywords` — sa **loading i error state-om**. Admin kampanje
stranica dobija **„Generiši kopiju (AI)"** dugme koje poziva `POST /ai/content`
(`/ml/ai/content`, `kind=campaign_copy`). Kad LLM nije dostupan, oba vraćaju
**template fallback** (`source="template"`, `fallback=true`) — nikad tihi fail.

## Ciljevi učenja

Do kraja dana treba da:

* objasnite **generative AI** u taksonomiji: pravila → heuristike → statistika →
  ML (predikcija) → **generacija** (LLM stvara novi tekst, ne klasifikuje/meri);
* definišete **strukturu izlaza** — Pydantic `SEOResponse` (`seo_title`,
  `seo_description`, `keywords`), umesto positional key mapping-a iz
  anti-pattern-a (gde su se ključevi mapirali po poziciji u listi);
* prompt-ujete LLM sa **system/user ulogama** i tražite JSON u tačnom formatu;
* **parsirate i validirate** output: `parse_json_output` (JSON iz raw teksta),
  `validate_required_fields` (po imenu), `validate_length` (Google limiti),
  `validate_product_facts` (naziv/kategorija se moraju pojaviti);
* retry-ate **bounded** broj puta i **fail-safe** — `generate_with_retry`
  broji pokušaje, posle iscrpljenih ide na template fallback (NIKAD `while True`);
* **apstrahujete model** iza `AIProvider` — app kod ne zna da li je lokalni
  TinyLlama ili external API;
* generišete **`generate_seo_metadata`**, **`generate_product_description`**,
  **`generate_campaign_copy`**, **`generate_keywords`**;
* uporedite **template vs LLM** output (length/field/fact provere) i objasnite
  šta validacija NE dokazuje.

## Preduslovi

* FastAPI/Pydantic (Days 3–4) — šeme i endpoint-i;
* Day 5 content/`products_text.csv` — katalog za template baseline i comparison;
* anti-pattern iz `current-materials/dm-ml/main.py` — ovo danas popravljaš.

## Teorija

### Generative AI u taksonomiji

| Klasa | Primer iz kursa | Ponašanje |
| --- | --- | --- |
| rule / heuristic | Day 2 RFM bucketi, Day 5 template | determinističko, objašnjivo, predvidljivo |
| statistical | Day 3 majority baseline, TF-IDF (Day 5) | merenje bez modela |
| ML — prediction | Day 3 logistic regression, Day 10 embeddings | predviđanje/merenje iz podataka |
| **generative AI** | **Day 11 LLM** | **stvara nov sadržaj — tekst koji nije postojao** |

Generative AI se razlikuje od svega do sada: ulaz je *opis zadatka* (prompt),
izlaz je *tekst*, a ista instrukcija može dati **različite** rezultate
(temperature). Zbog toga standardi kvaliteta iz ML-a (tačnost, preciznost) ovde
ne postoje direktno — umesto njih imamo **validaciju strukture i ograničenja**.

### Structured generation

LLM vraća *string*. Da bi servis mogao da ga koristi, tražimo JSON u tačnom
formatu (system prompt + instrukcija), pa izlaz **parsiramo** i **validiramo**:

```
class SEOResponse(BaseModel):
    seo_title: str
    seo_description: str
    keywords: list[str]
    source: str = "llm"
    fallback: bool = False
    fallback_reason: str | None = None
    validated: bool = True
    raw: str = ""
```

Imena polja su **eksplicitna** (`seo_title`, ne `title` po poziciji) — to je
direktna popravka anti-pattern-a:

```
# anti-pattern: ključevi se mapiraju PO POZICIJI (validKeys[i])
final[validKeys[i]] = jsonResponse[tempKeys[i]]   # puca pri najmanjoj promeni reda
```

### Tok danas: generacija → validacija → retry → fail-safe

```
POST /ai/seo
   └─ AIService.generate_seo_metadata(product)
        ├─ provider?  NE ──────────────► template fallback (source="template")
        ├─ provider.generate(prompt)
        │    └─ parse_json_output()        ── InvalidLLMJsonError → retry
        │    └─ validate_required_fields() ── InvalidLLMJsonError → retry
        │    └─ validate_length()          ── predugačak → retry
        │    └─ validate_product_facts()   ── naziv nedostaje → retry
        │    └─ schema.model_validate()    ── Pydantic (tipovi)
        └─ max_retries iscrpljen ──────────► GenerationFailSafeError → template fallback
```

Bounded retry znači **tačno** `max_retries + 1` pokušaja, pa prestani. Svaki
pokušaj *ponovo generiše* (LLM sa temperature > 0 može da da drugačiji izlaz).
Posle iscrpljenih pokušaja **fail-safe**: template baseline (`fallback_reason= "invalid_llm_output"`), nikad prazan odgovor, nikad nevalidiran odgovor.

### Tokeni, temperatura, halucinacija

* **Tokeni** — jedinice teksta koje model generiše; `max_tokens` ograničava
  dužinu izlaza (anti-pattern je koristio `max_new_tokens=1000`).
* **Temperature** — slučajnost izbora: 0 = gotovo deterministički, 1 = raznovrsno.
  Structured output obično koristi nisku temperaturu (0.3–0.5) da JSON ne
  „pobegne".
* **Halucinacija** — model može da generiše *plausibilan ali netačan* sadržaj
  (pogrešna cena, izmišljena specifikacija). Validacija hvata strukturu i
  očigledne propuste (naziv se ne pojavljuje), ali **ne** istinitost — to je
  ključna NOT-prove lekcija dana.

### Provider apstrakcija

App kod ne sme da zna koji je model:

```
class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.5) -> str: ...
    @abstractmethod
    def available(self) -> bool: ...
    @abstractmethod
    def descriptor(self) -> dict: ...

class LocalModelProvider(AIProvider): ...   # transformers pipeline (TinyLlama)
class ExternalProvider(AIProvider): ...     # OpenAI-compatible HTTP API
class DeepSeekProvider(ExternalProvider): ... # DeepSeek: https://api.deepseek.com, model deepseek-chat
```

`build_default_provider("auto")` bira: external ako je konfigurisan
(`AI_EXTERNAL_BASE_URL`/`AI_EXTERNAL_API_KEY`), inače local ako je model keširan,
inače `None` → **template-only režim** (fail-safe). Anti-pattern je imao
`pipeline("text-generation", model="TinyLlama/...")` direktno u ruti.

**Pravi provider: DeepSeek.** `AI_PROVIDER=deepseek` uključuje `DeepSeekProvider`
(OpenAI-kompatibilan API, `https://api.deepseek.com`, model `deepseek-chat`); ključ se čita
samo iz env-a `DEEPSEEK_API_KEY` i nikad se ne loguje (`descriptor()` ga ne sadrži). Bez
`AI_PROVIDER=deepseek` (ili bez ključa) servis ostaje u demo/template režimu — zato su svi
brojevi i izlazi u ovoj lekciji deterministički. `deepseek` se bira samo eksplicitno, nikad u `auto`.

```
AI_PROVIDER=deepseek dm-ml/.venv/bin/python "Day 11/examples/demo_generative.py"   # iz root-a kursa
cd dm-ml && .venv/bin/python ../../scripts/deepseek_live_check.py    # PLAĆENO; retry + validacija na pravim odgovorima
```

Primer jednog stvarnog pokretanja (2026-10-13). **LLM izlaz se menja od poziva do poziva** —
tvoj tekst, dužine i broj pokušaja biće drugačiji; stabilne su samo provere:

```
[3] generate_seo_metadata (LLM -> validacija -> fail-safe):
    source=deepseek  fallback=False  reason=None
    seo_title      : Smartphone Compact 686 - 5G OLED Dual Camera Black
    pokušaji: 1  greške: []  validacija: {... 'valid': True, 'title_len': 50, 'desc_len': 140}
```

Šta je pravi model pokazao: u jednom pokušaju naslov i opis nisu sadržali reč „Electronics”,
pa je `facts_ok=False` (validacija je to uhvatila). Zato servis sada validaciju radi *unutar*
bounded retry-ja (`generate_with_retry(..., validator=...)`): neuspela provera = novi pokušaj,
najviše `1 + max_retries`, pa template fallback. Kad smo namerno ograničili odgovor na
`max_tokens=8`, sva 3 pokušaja su vratila odsečen JSON → `GenerationFailSafeError` → fallback
`invalid_llm_output`. Kad smo tražili naslov od ~120 znakova, `title_ok=False` (106 > 60).

## API

### `POST /ai/seo`

Body: `{"product_name", "description", "category_name"}` → `SEOResponse`
(validiran). Primer (`curl` direktno na FastAPI `:3001`; iz frontenda isti poziv ide
kroz Nitro proxy kao `/ml/ai/seo`):

```
curl -s -X POST http://127.0.0.1:3001/ai/seo \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Smartphone Compact 686", "description": "5G smartphone with OLED display, dual camera and fast charging.", "category_name": "Electronics"}'
```

Odgovor (LLM ili template fallback):

```
{
  "seo_title": "Smartphone Compact 686 | Electronics",
  "seo_description": "Kupite Smartphone Compact 686. 5G smartphone with OLED display, dual camera and fast charging.",
  "keywords": ["smartphone", "compact", "686", "electronics", "5g"],
  "source": "template",
  "fallback": true,
  "fallback_reason": "model_unavailable",
  "validated": true,
  "raw": ""
}
```

### `POST /ai/content`

Body: `{"kind": "product_description"|"campaign_copy", …}` → `ContentResponse`
(`content`, `kind`, `source`, `fallback`, `fallback_reason`). Za
`campaign_copy` prosledi `campaign_name`/`campaign_goal`/`campaign_audience`.

### Failure handling (deo kursa)

* **Provider nije dostupan** → `200` sa template fallback-om
  (`fallback_reason="model_unavailable"`) — NIKAD tihi fail.
* **LLM output ne prođe validaciju** (nevalidan JSON, polja, dužina ili činjenice — svaka
  greška troši jedan pokušaj; bounded retry iscrpljen) → `200` sa template fallback-om
  (`fallback_reason="invalid_llm_output"`).
* **Nevalidan request** (prazan `product_name`, nepoznat `kind`) → `422`.

## Template vs LLM — poređenje (`Day 11/data/comparison.csv`)

Iste provere na obe strane (dužina / obavezna polja / product facts). Committed
uzorak koristi `--provider demo` — **scripted teaching double**, NIJE pravi LLM
(vidi `data/README.md` i `metadata.json`). Sa `--provider local/external` dobijaš
pravi LLM put; ako provider nije dostupan, generator to jasno upiše u metadata.

| product | method | source | seo\_title | title\_len | title\_ok | facts\_ok | valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Smartphone Compact 686 | template | template | Smartphone Compact 686 \| Electronics | 36 | ✓ | ✓ | ✓ |
| Smartphone Compact 686 | llm | demo:valid | Smartphone Compact 686 \| Electronics | 36 | ✓ | ✓ | ✓ |
| Novel Premium 556 | template | template | Novel Premium 556 \| Books | 25 | ✓ | ✓ | ✓ |
| Novel Premium 556 | llm | demo:length\_fail | Novel Premium 556 \| Books — najbolja cena online, kupi danas… | 94 | **✗** | ✓ | **✗** |
| Blender Classic 334 | template | template | Blender Classic 334 \| Home | 26 | ✓ | ✓ | ✓ |
| Blender Classic 334 | llm | demo:facts\_fail | Home — najbolje cene | 20 | ✓ | **✗** | **✗** |
| … | … | … | … | … | … | … | … |

Šta tabela kaže:

* **Template je uvek validan** — struktura je garantovana kodom (baseline).
* **LLM output može biti fluentan i nevalidan**: predugačak naslov (`94 > 60`)
  ili tekst koji uopšte ne pominje proizvod (facts fail).
* **Validacija hvata strukturu i ograničenja** — dužine, obavezna polja,
  prisustvo naziva/kategorije — **ne istinitost**. „Novel Premium 556 | Books —
  najbolja cena" može biti sasvim razuman naslov za pogrešan proizvod.

## Evaluacija (kako znamo da je dobro)

* **Oba endpoint-a vraćaju validiran, schema-conformant odgovor** —
  `response_model=SEOResponse/ContentResponse`; servis uvek vrati model
  (LLM ili template), nikad nevalidiran dict.
* **Retry je bounded i fail-safe** — `generate_with_retry` pozove providera
  tačno `max_retries + 1` puta pa baci `GenerationFailSafeError`; test
  `test_malformed_json_retried_then_rejected` broji pozive (= 3 za max\_retries=2).
* **Invalid LLM JSON se odbija** — `parse_json_output` baca
  `InvalidLLMJsonError`; testovi pokrivaju ne-JSON, nebalansiran JSON,
  ne-dict JSON, fenced JSON sa prozom.
* **`AIProvider` apstrahuje model** — `LocalModelProvider`/`ExternalProvider`
  dele interfejs; `build_default_provider` bira; app kod ne hard-koduje model.
* **Admin dugmad su wired** — create/update produkt form → `/ml/ai/seo`,
  kampanje → `/ml/ai/content`, sa loading/error state-om.
* **Template-vs-LLM poređenje je dokumentovano** — `comparison.csv` +
  tabela u README; generator je byte-for-byte (sha256 u metadata).
* **Full dm-ml suite prođe** — `.venv/bin/pytest app/tests` (9 testova, uključujući `app/tests/test_ai.py`).

## Česti bugovi

* **Beskonačan retry** — `while True` dok ne parsira (anti-pattern). Rešenje:
  `generate_with_retry` broji `max_retries`; posle toga fail-safe.
* **Positional key mapping** — `final[validKeys[i]] = jsonResponse[tempKeys[i]]`
  puca kad LLM promeni redosled ključeva. Rešenje: `validate_required_fields`
  po **imenu** + Pydantic šema.
* **Nema schema validacije** — LLM JSON se koristi „kako jeste". Rešenje:
  `validate_generated_output` (required → length → facts → `model_validate`).
* **Model hard-code-ovan u app kodu** — `pipeline("text-generation", ...)` u
  ruti. Rešenje: `AIProvider` + `build_default_provider`.
* **Predugačak naslov/opis** — LLM ignoriše „do 60 karaktera". Rešenje:
  `validate_length` + `length_limits` u validaciji (vežba: „tighten validation
  for a Google length limit").
* **Generisan tekst koji ne pominje proizvod** — halucinacija/promena teme.
  Rešenje: `validate_product_facts` (naziv/kategorija moraju da se pojave).
* **Tretiranje validacije kao dokaza istinitosti** — naslov koji prolazi sve
  provere može biti netačan. To je NOT-prove lekcija, ne bug.

## Šta rezultat NE dokazuje

* **Validan, fluentan SEO tekst nije garantovan kao istinit.** Validacija
  proverava *strukturu i ograničenja* (polja, dužine, prisustvo naziva) — ne da
  su navedene cene/specifikacije tačne. „Smartphone Compact 686 | Electronics" je
  validan i za potpuno izmišljen proizvod.
* **Generisana kopija može biti plausibilna i pogrešna.** LLM nema pristup
  stvarnom stanju zaliha, cenama ili istoriji kupca — on generiše *verovatne*
  rečenice, ne *tačne* podatke.
* **Demo provider nije pravi LLM.** Committed `comparison.csv` koristi
  `--provider demo` (scripted double) da deterministički prikaže šta validacija
  hvata. Da bi video *pravi* LLM, konfiguriši `AI_PROVIDER=deepseek|local|external` i
  regeneriši — a i tada uspeh znači „strukturno validno", ne „tačno".
* **Template-vs-LLM poređenje na 6 proizvoda nije benchmark.** To je
  *metodologija* evaluacije; drugačiji katalog/prompti mogu da promene odnos.
* **Generative AI nije personalizacija.** Kopija je ista za sve korisnike
  (osim ako joj eksplicitno daš kontekst) — personalizacija je Day 8/9/12.

## Vežbe

1. **Uradi lab** — u `Day 11/lab/` napiši `parse_json_output`,
   `validate_required_fields`, `validate_length`, `validate_product_facts`,
   `generate_with_retry` i `ExternalProvider`, pa proveri `test_lab.py`.
2. **Dodaj novu generacionu funkciju** — `generate_campaign_copy` već postoji u
   `app/services/ai.py`; napiši svoju `generate_email_subject(product, offer)`
   ili proširi prompt kampanje (vežba iz DAY-BRIEFS-a).
3. **Tighten validation za Google length limit** — povećaj `seo_title` limit
   na 70 i pogledaj koje demo:length\_fail redove bi to „spasilo"; zatim vrati
   na 60. (Da li title od 94 karaktera postaje validan? Ne — limit je na 70.)
4. **Implementiraj `ExternalProvider` sam** — u lab-u, pa ga testiraj sa
   monkeypatch-anim `http_post`; zatim konfiguriši pravi API i pozovi
   `POST /ai/seo`.
5. **Dodaj test za malformed JSON** — u `app/tests/test_ai.py` napiši novi
   test gde provider vrati `{"seo_title": "x"` (nebalansiran) — da li
   `generate_with_retry` broji retry i baca fail-safe?
6. **Promeni temperaturu** — u `AIService.generate_seo_metadata` prosledi
   `temperature=1.0` i pokreni dva puta: da li je JSON izlaz stabilniji na
   `temperature=0.3`? (Structured output preferira nisku temperaturu.)
7. **Uporedi sa Day 5 template tekstom** — za isti proizvod uporedi
   `template_product_description` (Day 11) sa Day 5 `products_text.csv`
   opisom. Gde je LLM/template bolji? (Oba su tekst; jedno je pravilo, drugo
   je model.)
8. **Regeneriši comparison sa pravim providerom** — `AI_PROVIDER=external`
   (ili `local` sa keširanim modelom) + `python -m app.data.generate_ai_comparison --provider auto`; uporedi `metadata.json` summary sa demo uzorkom.
9. **Latency** — izmeri vreme `provider.generate(...)` za lokalni i za external
   provider. Ne pretpostavljajte ko je brži: TinyLlama na CPU-u je često *sporiji* od
   hosted API-ja, a API dodaje mrežnu latenciju i rate limit. Zašto retry mora da bude
   *bounded* (svaki pokušaj košta sekunde)?

## Sažetak

Napravio si **structured generative-AI servis**: `AIProvider` apstrakciju
(`LocalModelProvider`/`ExternalProvider`), Pydantic šeme (`SEOResponse`/
`ContentResponse`), **validaciju** (`parse_json_output`, `validate_required_fields`,
`validate_length`, `validate_product_facts`, `validate_generated_output`),
**bounded retry + fail-safe** (`generate_with_retry` → `GenerationFailSafeError`
→ template fallback) i generaciju SEO meta, opisa proizvoda, prodajne kopije i
ključnih reči — izložene kroz `POST /ai/seo` i `POST /ai/content` i integrisane u
CMS admin (Generate dugmad sa loading/error state-om). Dodao si i **template-vs-LLM
poređenje** (`Day 11/data/comparison.csv`). Centralna lekcija: *validacija
proverava strukturu i ograničenja, ne istinitost — fluentan tekst može biti
potpuno netačan, a retry mora biti bounded da bi sistem bio predvidiv i fail-safe*.
Sledeći korak (Day 12) povezuje sve module u capstone.

---

<!-- page_id 433 order 1 -->
## [Page] Primeri i resursi

## Primeri i resursi

### data/comparison.csv

```
product_id,name,method,source,seo_title,seo_description,keywords,title_len,desc_len,title_ok,desc_ok,fields_ok,facts_ok,valid
1,Smartphone Compact 686,template,template,Smartphone Compact 686 | Electronics,"Kupite Smartphone Compact 686. 5G smartphone with OLED display, dual camera and fast charging. Compact line, black.",smartphone | compact | 686 | electronics | 5g,36,115,True,True,True,True,True
1,Smartphone Compact 686,llm,demo:valid,Smartphone Compact 686 | Electronics,Kupite Smartphone Compact 686 — Electronics proizvod po najboljoj ceni.,smartphone | compact | 686 | kupi | online,36,71,True,True,True,True,True
43,Novel Premium 556,template,template,Novel Premium 556 | Books,"Kupite Novel Premium 556. Bestselling contemporary novel, paperback. Premium line, red.",novel | premium | 556 | books | bestselling,25,87,True,True,True,True,True
43,Novel Premium 556,llm,demo:length_fail,"Novel Premium 556 | Books — najbolja cena online, kupi danas, uštedi više, vreme je ograničeno",Kupite Novel Premium 556 — Books proizvod po najboljoj ceni i uz brzu dostavu.,novel | premium | 556 | kupi | online,94,78,False,True,True,True,False
85,Blender Classic 334,template,template,Blender Classic 334 | Home,"Kupite Blender Classic 334. Kitchen blender for smoothies and soups. Classic line, beige.",blender | classic | 334 | home | kitchen,26,89,True,True,True,True,True
85,Blender Classic 334,llm,demo:facts_fail,Home — najbolje cene,Otkrijte najbolje proizvode po sjajnim cenama i brzu dostavu.,blender | classic | 334 | kupi | online,20,61,True,True,True,False,False
127,Building Blocks Premium 126,template,template,Building Blocks Premium 126 | Toys,"Kupite Building Blocks Premium 126. Building blocks set, creative construction toy. Premium line, grey.",building | blocks | premium | 126 | toys,34,103,True,True,True,True,True
127,Building Blocks Premium 126,llm,demo:valid,Building Blocks Premium 126 | Toys,Kupite Building Blocks Premium 126 — Toys proizvod po najboljoj ceni.,building | blocks | premium | kupi | online,34,69,True,True,True,True,True
169,Sofa Essential 990,template,template,Sofa Essential 990 | Furniture,"Kupite Sofa Essential 990. Three-seat sofa, fabric upholstery. Essential line, beige.",sofa | essential | 990 | furniture | three,30,85,True,True,True,True,True
169,Sofa Essential 990,llm,demo:length_fail,"Sofa Essential 990 | Furniture — najbolja cena online, kupi danas, uštedi više, vreme je ograničeno",Kupite Sofa Essential 990 — Furniture proizvod po najboljoj ceni i uz brzu dostavu.,sofa | essential | 990 | kupi | online,99,83,False,True,True,True,False
211,Acoustic Guitar Everyday 144,template,template,Acoustic Guitar Everyday 144 | Music,"Kupite Acoustic Guitar Everyday 144. Acoustic guitar, spruce top. Everyday line, blue.",acoustic | guitar | everyday | 144 | music,36,86,True,True,True,True,True
211,Acoustic Guitar Everyday 144,llm,demo:facts_fail,Music — najbolje cene,Otkrijte najbolje proizvode po sjajnim cenama i brzu dostavu.,acoustic | guitar | everyday | kupi | online,21,61,True,True,True,False,False
```

### data/metadata.json

```
{
  "dataset": "dm_ai_comparison_v1",
  "description": "Template-vs-LLM SEO poređenje (Day 11): za uzorak proizvoda generiše template SEO (rule/heuristic baseline) i LLM SEO (preko AIProvider-a) i proverava oba kroz iste provere (Google dužine, obavezna polja, product facts). Validnost ovde meri STRUKTURU i ograničenja, NE istinitost teksta.",
  "source": "derived",
  "derived_from": {
    "products": "Day 5/data/products_text.csv",
    "module": "app.data.generate_ai_comparison",
    "function": "build_comparison",
    "templates": "app.services.templates",
    "ai_service": "app.services.ai"
  },
  "provider_requested": "demo",
  "provider_used": "demo",
  "provider_note": "demo = scripted teaching double (deterministički, offline, NIJE pravi LLM). Varijante demo:valid (prolazi), demo:length_fail (predugačak naslov), demo:facts_fail (naziv se ne pojavljuje) — izabrane po poziciji u uzorku da pokažu šta validacija hvata. local/external = pravi provider; ako nije dostupan koristi se demo (provider_used to beleži).",
  "parameters": {
    "sample": 6,
    "title_max": 60,
    "desc_max": 155,
    "required_fields": [
      "seo_title",
      "seo_description",
      "keywords"
    ]
  },
  "columns": {
    "product_id": "int, stabilan ID proizvoda",
    "name": "str, naziv proizvoda",
    "method": "template | llm",
    "source": "ko je generisao red: template | demo | local | external | '<name> (invalid)'",
    "seo_title": "str, generisani SEO naslov",
    "seo_description": "str, generisani SEO opis",
    "keywords": "str, ključne reči spojene sa ' | '",
    "title_len": "int, len(seo_title)",
    "desc_len": "int, len(seo_description)",
    "title_ok": "bool, title_len <= 60",
    "desc_ok": "bool, desc_len <= 155",
    "fields_ok": "bool, sva obavezna polja prisutna",
    "facts_ok": "bool, naziv/kategorija se pojavljuju u tekstu",
    "valid": "bool, sve provere prolaze"
  },
  "summary": {
    "rows": 12,
    "template_valid": 6,
    "llm_valid": 2,
    "title_over_60": 2,
    "desc_over_155": 0,
    "facts_missing": 2
  },
  "manifest": {
    "sha256": {
      "comparison.csv": "55197f8f0400f1d9f25b682a58d917166f13877f51bcb1dc9806971e77809336"
    }
  }
}
```

### data/README.md

# Day 11 podaci — template-vs-LLM SEO poređenje

Deterministički, **byte-for-byte reproduktivni** `comparison.csv` **izveden** iz
Day 5 kataloga (ne duplira ga). Kompletna dokumentacija (izvor, provider,
parametri, counts, sha256) je u `metadata.json`.

## Fajlovi

| Fajl | Sadržaj | Oblik |
| --- | --- | --- |
| `comparison.csv` | **template vs LLM SEO** na 6 proizvoda — za svaki: template red (rule/heuristic baseline) i llm red (generisani), oba kroz iste provere (dužine / obavezna polja / product facts) | 12 redova |
| `metadata.json` | izvor, provider, parametri, summary, sha256 | — |

## Kako nastaje (izvedena tabela)

* Ulaz: `Day 5/data/products_text.csv` (katalog sa nazivom, opisom, kategorijom).
* Za svaki proizvod iz determinističkog uzorka (svaki 42-i red, prvih 6):
  1. **template** red: `template_seo_metadata` (`app.services.templates`) —
     rule/heuristic baseline, uvek strukturno validan;
  2. **llm** red: `AIProvider.generate(seo_prompt(product))` → `parse_json_output`
     → iste provere (`compare_outputs`). Provider se bira preko
     `--provider demo|local|external|auto`.
* Generator: `app/data/generate_ai_comparison.py`.

## `comparison.csv` — šta poredi i šta validacija hvata

Provere su iste za obe strane (`compare_outputs`):

| Kolona | Značenje |
| --- | --- |
| `method` | `template` | `llm` |
| `source` | ko je generisao red: `template`, `demo:valid`, `demo:length_fail`, `demo:facts_fail`, `local`, `external`, `<name> (invalid)` |
| `title_len` / `desc_len` | dužine generisanog SEO naslova / opisa |
| `title_ok` | `title_len <= 60` (Google limit) |
| `desc_ok` | `desc_len <= 155` (Google limit) |
| `fields_ok` | sva obavezna polja prisutna (`seo_title`, `seo_description`, `keywords`) |
| `facts_ok` | naziv/kategorija proizvoda se pojavljuju u tekstu (slaba provera istinitosti) |
| `valid` | sve provere prolaze |

Committed uzorak koristi `--provider demo` — **scripted teaching double**
(NAPIŠEN U `metadata.json`), ne pravi LLM. Varijante (po poziciji u uzorku):

| Varijanta | Šta pokazuje |
| --- | --- |
| `demo:valid` | naslov kratak i sadrži naziv → prolazi sve provere |
| `demo:length_fail` | naslov sadrži naziv ali je **predugačak** (90+ > 60) → `title_ok=False` |
| `demo:facts_fail` | generički naslov/opis, **naziv se nigde ne pojavljuje** → `facts_ok=False` |

Template redovi su uvek `valid=True` (struktura je garantovana kodom), dok
LLM redovi pokazuju šta validacija mora da uhvati.

## Reprodukcija

```
cd dm-ml
.venv/bin/python -m app.data.generate_ai_comparison --provider demo   # committed (offline)
.venv/bin/python -m app.data.generate_ai_comparison --provider auto   # pravi provider ako je konfigurisan
.venv/bin/python -m app.data.generate_ai_comparison --provider external --sample 10
```

Isti provider + isti ulaz → identični fajlovi (sha256 u `metadata.json`).
Ako pokušaš `local`/`external` bez konfigurisanog providera, generator upozorava
i koristi demo (to beleži `metadata.provider_used`).

### examples/demo\_generative.py

```
"""Demo: structured generative-AI service (Day 11).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 11/examples/demo_generative.py"

Prikazuje:
  1) **AIProvider apstrakciju** — koji provider je aktivan (auto/local/external
     ili None -> template-only režim);
  2) **template baseline** — ``template_seo_metadata`` (rule/heuristic);
  3) **LLM put** — ``generate_seo_metadata`` (validacija + bounded retry +
     fail-safe; bez konfigurisanog modela vidljiv je template fallback);
  4) **fail-safe u praksi** — provider koji uvek vraća ne-JSON -> bounded retry
     (3 poziva) pa template fallback (``fallback_reason="invalid_llm_output"``);
  5) **content** — ``generate_product_description`` i ``generate_campaign_copy``;
  6) **template-vs-LLM poređenje** — summary iz ``Day 11/data/comparison.csv``
     (gde validacija hvata length/facts).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.ai import (
    AIService,
    AIProvider,
    GenerationFailSafeError,
    InvalidLLMJsonError,
    generate_with_retry,
    parse_json_output,
    validate_required_fields,
)
from app.services.ai import SEOResponse

PRODUCT = {
    "name": "Smartphone Compact 686",  # proizvod 1 iz Day 5 kataloga
    "description": "5G smartphone with OLED display, dual camera and fast charging. Compact line, black.",
    "category": "Electronics",
}
CAMPAIGN = {
    "name": "VIP reaktivacija",
    "goal": "Reaktiviraj najvrednije K-Means segmente",
    "target_segments": "segment_2, segment_3",
}


class _BrokenProvider(AIProvider):
    """Testni double koji uvek vrati ne-JSON (demo bounded retry + fail-safe)."""

    def available(self):
        return True

    def descriptor(self):
        return {"name": "broken"}

    def generate(self, prompt, **kwargs):
        return "I'm sorry, I cannot generate valid JSON right now."


def main() -> None:
    print("=== Day 11 — Structured Generative-AI Marketing Service ===\n")
    svc = AIService()
    print(f"[1] Aktivni provider: {svc.provider!r}  "
          f"(None = template-only režim — LLM nije konfigurisan/keširan)")
    print()

    # --- 2) Template baseline ----------------------------------------------- #
    print("[2] Template SEO baseline (rule/heuristic):")
    tpl = svc.template_seo(PRODUCT)
    print(f"    seo_title      : {tpl.seo_title}")
    print(f"    seo_description: {tpl.seo_description}")
    print(f"    keywords       : {tpl.keywords}")
    print()

    # --- 3) LLM put (sa fail-safe) ------------------------------------------ #
    print("[3] generate_seo_metadata (LLM -> validacija -> fail-safe):")
    seo = svc.generate_seo_metadata(PRODUCT)
    print(f"    source={seo.source}  fallback={seo.fallback}  "
          f"reason={seo.fallback_reason}")
    print(f"    seo_title      : {seo.seo_title}")
    print(f"    seo_description: {seo.seo_description}")
    print(f"    keywords       : {seo.keywords}")
    if svc.last_trace:  # samo kad je pravi provider pozvan (npr. AI_PROVIDER=deepseek)
        print(f"    pokušaji: {len(svc.last_trace)}  greške: {[e for e in svc.last_trace if e]}  "
              f"validacija: {svc.last_checks}")
    print()

    # --- 4) Fail-safe u praksi (bounded retry) ------------------------------- #
    print("[4] Bounded retry: broken provider (uvek ne-JSON, max_retries=2):")
    broken = _BrokenProvider()
    try:
        result = generate_with_retry(
            broken, "prompt", schema=SEOResponse,
            required=["seo_title", "seo_description", "keywords"],
            max_retries=2,
        )
        print(f"    (neočekivano uspelo: {result})")
    except GenerationFailSafeError as exc:
        print(f"    GenerationFailSafeError posle 3 pokušaja: {str(exc)[:80]}...")
    print("    (servis tada vraća template fallback — probaj svojom rukom)")
    print()

    # --- 5) Content ---------------------------------------------------------- #
    print("[5] Content generation (LLM -> template fallback):")
    desc = svc.generate_product_description(PRODUCT)
    print(f"    product_description [{desc.source}] fallback={desc.fallback}: {desc.content[:90]}…")
    copy = svc.generate_campaign_copy(CAMPAIGN)
    print(f"    campaign_copy      [{copy.source}] fallback={copy.fallback}: {copy.content[:90]}…")
    print()

    # --- 6) Template-vs-LLM poređenje ---------------------------------------- #
    print("[6] Template vs LLM (Day 11/data/comparison.csv):")
    comp_path = Path(__file__).resolve().parents[1] / "data" / "comparison.csv"
    if comp_path.exists():
        import pandas as pd

        comp = pd.read_csv(comp_path)
        for _, row in comp.iterrows():
            badge = "OK" if row["valid"] else "FAIL"
            fails = []
            if not row["title_ok"]:
                fails.append(f"title={row['title_len']}>60")
            if not row["desc_ok"]:
                fails.append(f"desc={row['desc_len']}>155")
            if not row["fields_ok"]:
                fails.append("fields")
            if not row["facts_ok"]:
                fails.append("facts")
            print(f"    {row['method']:8s} {row['source']:16s} {row['seo_title'][:34]:34s} "
                  f"[{badge}] {', '.join(fails) if fails else ''}")
    else:
        print("    comparison.csv nije generisan — pokreni "
              "`python -m app.data.generate_ai_comparison`")
    print()

    print("API: POST /ai/seo · POST /ai/content")
    print("Lab: Day 11/lab — parse_json_output, validate_*, generate_with_retry, ExternalProvider")


if __name__ == "__main__":
    main()
```

### lab/README.md

# Day 11 lab — structured generative-AI service (student piše)

Kursni modul `dm-ml/app/services/ai.py` sadrži punu verziju (AIProvider,
`parse_json_output`, `validate_*`, `generate_with_retry`, `ExternalProvider`).
U ovom lab-u **ti ih pišeš sam** — na malim, ručno napravljenim strukturama —
da razumeš *šta* structured generation radi pre nego što dotakneš pravi LLM.

Ne menjaš `dm-ml` — radiš u `starter.py` i proveravaš rešenje sa `test_lab.py`.

## Zadaci (`starter.py`)

1. `parse_json_output(raw)` — izvuci prvi JSON objekat iz raw LLM teksta
   (preskoči `json` fence-ove i uvodni/prazeći tekst). Ne-parse-abilan
   output -> `InvalidLLMJsonError`. **Ovo je osnova invalid-LLM-json rejection-a.**
2. `validate_required_fields(data, required)` — obavezna polja **po imenu**
   (anti-pattern je mapirao ključeve po poziciji — `validKeys[i]`). Nedostaje
   polje -> `InvalidLLMJsonError`.
3. `validate_length(value, max_len)` — `len(str(value)) <= max_len`
   (npr. Google limit za SEO naslov = 60).
4. `validate_product_facts(generated_text, product)` — da li tekst pominje
   naziv/kategoriju proizvoda; vraća listu nedostajućih fact-ova
   (`name` / `category`). Slaba provera „istinitosti".
5. `generate_with_retry(provider, prompt, max_retries=2)` — generiši +
   validiraj JSON, **bounded** retry; posle `max_retries + 1` pokušaja ->
   `GenerationFailSafeError` (nikad bezkonačno `while True`).
6. `http_post(url, payload, headers)` + `ExternalProvider` — OpenAI-compatible
   HTTP provider iza iste `AIProvider` apstrakcije. `generate` šalje
   `/chat/completions` i vraća `choices[0].message.content`.

## Pokretanje

```
cd "Day 11/lab"
# svoje rešenje:
python3 -m pytest test_lab.py
# referentno rešenje:
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Vežba (malformed JSON → retry → fail-safe)

U `test_lab.py` pogledaj `test_malformed_json_retried_then_rejected`: provider
uvek vraća ne-JSON, `max_retries=2` — očekivano je **tačno 3** poziva providera
(1 + 2 retry-ja), pa `GenerationFailSafeError`. To je razlika u odnosu na
anti-pattern iz `current-materials/`, koji je radio `while True` bez limita.
Ako umesto `<=` pišeš `<` u petlji, retry postaje 4+ poziva — test će pasti.

### lab/starter.py

```
"""Starter za Day 11 lab — structured generative-AI service (student piše).

Kursni modul ``dm-ml/app/services/ai.py`` već sadrži punu verziju ovoga
(``parse_json_output``, ``validate_*``, ``generate_with_retry``,
``ExternalProvider``). U ovom lab-u **ti ih pišeš sam** — na malim, ručno
napravljenim strukturama — da razumeš *šta* structured generation radi pre
nego što dotakneš pravi LLM (DAY-BRIEFS: unbounded retry, positional key
mapping i izostanak validacije su česti bagovi — ovde ih svesno popravljaš).

Ne menjaš ``dm-ml`` — radiš u ovom fajlu i proveravaš rešenje sa
``test_lab.py``:

    cd "Day 11/lab"
    python3 -m pytest test_lab.py              # tvoje rešenje
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # referentno

Fajl je samostalan (bez importa iz ``dm-ml``) — pišeš čistu Python logiku.
"""

import json
import re


# --------------------------------------------------------------------------- #
# Greške — iste uloge kao u dm-ml (InvalidLLMJsonError -> retry, posle toga
# GenerationFailSafeError -> template fallback)
# --------------------------------------------------------------------------- #
class InvalidLLMJsonError(Exception):
    """LLM output se ne može protumačiti kao validan JSON objekat."""


class GenerationFailSafeError(Exception):
    """Iscrpljeni su bounded retry pokušaji — pozivalac prelazi na fail-safe."""


# --------------------------------------------------------------------------- #
# AIProvider apstrakcija
# --------------------------------------------------------------------------- #
class AIProvider:
    """Apstrakcija generativnog modela — ``generate(prompt) -> str``.

    Aplikacioni kod NE sme da zna koji je model iza: ``LocalModelProvider``
    (TinyLlama) i ``ExternalProvider`` (HTTP API) dele isti interfejs.
    """

    def generate(self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.5) -> str:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError

    def descriptor(self) -> dict:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# 1) parse_json_output — izvuci JSON iz raw LLM teksta
# --------------------------------------------------------------------------- #
def parse_json_output(raw: str) -> dict:
    """Vadi prvi JSON objekat iz raw LLM outputa.

    LLM često doda ```json``` fence-ove, uvodni/prazeći tekst ili komentare.
    Preskoči sve to i vrati **dict**. Ako objekat ne postoji ili nije
    parsabilan -> ``InvalidLLMJsonError`` (ovo je slučaj koji bounded retry
    ponavlja).

    Anti-pattern (``current-materials/``) je ovde radio ``while True`` +
    ``json.loads`` bez ikakvog limita — ovde funkcija samo **prijavi** grešku,
    a ``generate_with_retry`` broji pokušaje.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) validate_required_fields — po imenu polja, ne po poziciji
# --------------------------------------------------------------------------- #
def validate_required_fields(data: dict, required: list[str]) -> None:
    """Proveri da su sva ``required`` polja prisutna (po imenu).

    Nedostajuće polje -> ``InvalidLLMJsonError`` sa imenima koja fale.

    Anti-pattern je mapirao ključeve **po poziciji** (``validKeys[i]``) —
    šema očekuje ``seo_title``/``seo_description``/``keywords``, a ti moraš
    da proveriš **imena** polja, ne redosled.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) validate_length — Google limit
# --------------------------------------------------------------------------- #
def validate_length(value, max_len: int) -> bool:
    """Da li je ``len(str(value)) <= max_len`` (npr. seo_title <= 60)."""
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 4) validate_product_facts — slaba provera „istinitosti"
# --------------------------------------------------------------------------- #
# Minimalni stopwordi (lab koristi mali skup; dm-ml ima veći).
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "he", "in", "is", "it", "of", "on", "or", "that", "the", "to",
    "was", "were", "will", "with", "i", "you", "your", "we", "za", "i",
    "je", "na", "u", "se", "od", "sa", "sve", "kupite", "kupovina",
}


def _significant_tokens(text: str) -> list[str]:
    return [
        t.lower()
        for t in re.findall(r"[a-z0-9čćžšđ]+", str(text), re.IGNORECASE)
        if t.lower() not in STOPWORDS and len(t) > 1
    ]


def validate_product_facts(generated_text: str, product: dict) -> list[str]:
    """Product facts: da li tekst pominje naziv/kategoriju proizvoda.

    Vraća listu nedostajućih fact-ova (``name`` / ``category``). Proizvod bez
    naziva ili kategorije -> taj fact se preskače.

    Ovo je **slaba provera istinitosti**: prisustvo tokena nije dokaz da je
    tekst tačan (vidi README — „Šta rezultat NE dokazuje"), ali odsustvo
    jeste jak signal halucinacije (generisao si tekst koji uopšte ne pominje
    proizvod).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 5) generate_with_retry — bounded retry + fail-safe
# --------------------------------------------------------------------------- #
def generate_with_retry(provider: AIProvider, prompt: str, *, max_retries: int = 2, **kwargs) -> dict:
    """Generiši + validiraj JSON, sa **bounded** retry.

    Svaki pokušaj: ``provider.generate(prompt)`` -> ``parse_json_output`` ->
    ``validate_required_fields`` (SEO šema). Neuspeh se ponavlja do
    ``max_retries`` puta — **ne bezkonačno** (anti-pattern je radio
    ``while True``). Posle iscrpljenih pokušaja -> ``GenerationFailSafeError``,
    a pozivalac prelazi na template fallback (fail-safe).

    Vraća validiran ``dict`` (parsiran JSON).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 6) http_post + ExternalProvider — model iza apstrakcije
# --------------------------------------------------------------------------- #
def http_post(url: str, payload: dict, headers: dict) -> tuple[int, str]:
    """Pošalji POST JSON i vrati ``(status_code, response_text)``.

    HTTP greške (4xx/5xx) vraćaju status + telo; mrežne greške bacaju
    ``ConnectionError``. Testovi zamenjuju ovu funkciju da ne idu na mrežu.
    """
    # TODO: implementiraj (urllib.request)
    raise NotImplementedError


class ExternalProvider(AIProvider):
    """Provider preko OpenAI-compatible HTTP API-ja (``/chat/completions``).

    ``generate`` šalje ``{"messages": [{"role": "user", "content": prompt}],
    ...}`` i vraća ``choices[0].message.content``.
    """

    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4o-mini"):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model or "gpt-4o-mini"

    def available(self) -> bool:
        # TODO: dostupan ako su base_url i api_key konfigurisani
        raise NotImplementedError

    def descriptor(self) -> dict:
        # TODO: {"name": "external", "base_url": ..., "model": ...}
        raise NotImplementedError

    def generate(self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.5) -> str:
        # TODO: POST /chat/completions preko http_post; status != 200 -> raise;
        # inače izvuci choices[0].message.content i vrati strip()-ovano
        raise NotImplementedError
```

### lab/test_lab.py

```
import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import json


class Scripted(lab.AIProvider):
    def __init__(self, outputs):
        self.outputs = list(outputs); self.calls = 0

    def generate(self, prompt, **kw):
        self.calls += 1
        return self.outputs[min(self.calls - 1, len(self.outputs) - 1)]

    def available(self):
        return True

    def descriptor(self):
        return {"name": "scripted"}


GOOD = '```json\n{"seo_title": "T", "seo_description": "D", "keywords": ["k"]}\n``` hvala!'


def test_parse_json_output():
    assert lab.parse_json_output(GOOD)["seo_title"] == "T"
    assert lab.parse_json_output('Evo: {"a": {"b": 1}} kraj') == {"a": {"b": 1}}
    with pytest.raises(lab.InvalidLLMJsonError):
        lab.parse_json_output("nema json-a")


def test_validators():
    with pytest.raises(lab.InvalidLLMJsonError):
        lab.validate_required_fields({"seo_title": 1}, ["seo_title", "keywords"])
    lab.validate_required_fields({"keywords": 1, "seo_title": 2}, ["seo_title", "keywords"])  # redosled nebitan
    assert lab.validate_length("x" * 60, 60) and not lab.validate_length("x" * 61, 60)
    p = {"name": "Lamp 1952", "category": "Home"}
    assert lab.validate_product_facts("Home — najbolje cene", p) == ["name"]
    assert lab.validate_product_facts("Lamp 1952 | Home", p) == []


def test_malformed_json_retried_then_rejected():
    prov = Scripted(["I'm sorry"])
    with pytest.raises(lab.GenerationFailSafeError):
        lab.generate_with_retry(prov, "p", max_retries=2)
    assert prov.calls == 3


def test_retry_recovers():
    prov = Scripted(["junk", GOOD])
    assert lab.generate_with_retry(prov, "p", max_retries=2)["keywords"] == ["k"] and prov.calls == 2


def test_external_provider_without_network(monkeypatch):
    sent = {}

    def fake_post(url, payload, headers):
        sent.update(url=url, payload=payload, headers=headers)
        return 200, json.dumps({"choices": [{"message": {"content": "  hi  "}}]})
    monkeypatch.setattr(lab, "http_post", fake_post)
    p = lab.ExternalProvider("https://api.example.com/v1/", "sk-test", "m")
    assert p.available() and p.descriptor() == {"name": "external", "base_url": "https://api.example.com/v1", "model": "m"}
    assert p.generate("x") == "hi" and sent["url"].endswith("/chat/completions")
    assert not lab.ExternalProvider("", "").available()
    monkeypatch.setattr(lab, "http_post", lambda *a: (500, "err"))
    with pytest.raises(Exception):
        p.generate("x")
```

### lab/reference_solutions.py

```
"""Referentno rešenje Day 11 lab-a."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from starter import (STOPWORDS, AIProvider, GenerationFailSafeError, InvalidLLMJsonError,  # noqa: F401
                     _significant_tokens)
import starter as _s

SEO_FIELDS = ["seo_title", "seo_description", "keywords"]


def parse_json_output(raw):
    if not isinstance(raw, str):
        raise InvalidLLMJsonError("output nije string")
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", raw):
        try:
            obj, _ = dec.raw_decode(raw[m.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    raise InvalidLLMJsonError("nema validnog JSON objekta")


def validate_required_fields(data, required):
    miss = [f for f in required if f not in data]
    if miss:
        raise InvalidLLMJsonError(f"nedostaju polja: {', '.join(miss)}")


def validate_length(value, max_len):
    return len(str(value)) <= max_len


def validate_product_facts(generated_text, product):
    toks = set(_significant_tokens(generated_text)); missing = []
    for fact in ("name", "category"):
        need = _significant_tokens(product.get(fact) or "")
        if need and not set(need) <= toks:
            missing.append(fact)
    return missing


def generate_with_retry(provider, prompt, *, max_retries=2, **kwargs):
    last = None
    for _ in range(max_retries + 1):          # 1 pokušaj + max_retries ponavljanja
        try:
            data = parse_json_output(provider.generate(prompt))
            validate_required_fields(data, kwargs.get("required", SEO_FIELDS))
            return data
        except Exception as e:
            last = e
    raise GenerationFailSafeError(f"iscrpljeno {max_retries + 1} pokušaja: {last}")


def http_post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except urllib.error.URLError as e:
        raise ConnectionError(str(e.reason)) from e


class ExternalProvider(_s.ExternalProvider):
    def available(self):
        return bool(self.base_url and self.api_key)

    def descriptor(self):
        return {"name": "external", "base_url": self.base_url, "model": self.model}

    def generate(self, prompt, *, max_tokens=256, temperature=0.5):
        status, body = http_post(f"{self.base_url}/chat/completions",
                                 {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                                  "max_tokens": max_tokens, "temperature": temperature},
                                 {"Authorization": f"Bearer {self.api_key}"})
        if status != 200:
            raise RuntimeError(f"HTTP {status}")
        return json.loads(body)["choices"][0]["message"]["content"].strip()
```
