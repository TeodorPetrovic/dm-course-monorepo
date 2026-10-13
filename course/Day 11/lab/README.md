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
