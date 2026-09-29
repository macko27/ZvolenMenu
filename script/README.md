# Test menu reštaurácie ID 1

Skript načíta iba záznam s `Id = 1`, použije jeho URL zo stĺpca `Website` a
vypíše nájdené menu ako JSON. Do JSON pridá aktuálny dátum a deň v slovenčine.
Databázu nemení.

```powershell
.\script\.venv\Scripts\python.exe -m pip install -r .\script\requirements.txt
.\script\.venv\Scripts\python.exe .\script\main.py
```

Parser používa API Open WebUI na `https://llm.ai.e-infra.cz/v1/` s modelom
`qwen3.5` (vie čítať aj obrázky, takže zvláda menu vo forme fotografie).

## API kľúč

Kľúč vygeneruješ v Open WebUI: Settings → Account (Účet) → API keys →
Generate new API key. Nastav ho ako premennú prostredia `api_key` (napr. v
run configuration IDE), prípadne do súboru `script/.env` — nie do zdrojového
kódu:

```
api_key=TVOJ_API_KĽÚČ
```

Súbor `.env` je gitignorovaný.

## Database

The script reads restaurant ID 1 from the same PostgreSQL database as the
backend (default `localhost:5432`, database `zvolenmenu`, user `postgres`,
password `postgres`). Connection can be overridden via environment variables
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` or the same keys in
`script/.env`.

Skript odošle na API iba text načítanej stránky a najviac 5 obrázkov z nej
(každý do 5 MB). Databázu nemení a výsledok naďalej vypisuje ako JSON.

Stránka U Alexa zverejňuje iba aktuálne menu, nie samostatné menu pre všetky
dni. Skript preto automaticky označí výsledok dnešným dátumom; staršie alebo
budúce menu z tejto URL nie je možné vybrať.
