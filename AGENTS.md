# AGENTS.md

Web app showing daily menus of restaurants in Zvolen, Slovakia. UI text and code comments are in Slovak — preserve Slovak diacritics.

## Layout

- `backend/` — ASP.NET Core 8 Web API (C#), EF Core + SQLite. Single project `src/ZvolenMenu.Api/`, solution at `backend/ZvolenMenu.sln`.
- `frontend/` — React 19 + TypeScript + Vite, Leaflet map. No test framework.
- `script/` — Python scraper that parses restaurant websites into menu JSON using a local LLM.

## Running the app

Both must run together; the Vite dev server proxies `/api` to the backend.

```bash
# Backend — http://localhost:5089
cd backend/src/ZvolenMenu.Api && dotnet run

# Frontend — http://localhost:5173
cd frontend && npm install && npm run dev
```

CORS is locked to `http://localhost:5173` — the frontend must be served from that origin.

## Database

- PostgreSQL, connection string in `backend/src/ZvolenMenu.Api/appsettings.json` (`ConnectionStrings:Default`, defaults to `localhost:5432`, database `zvolenmenu`, user `postgres`).
- Database and tables are created at startup via `EnsureCreatedAsync` plus manual `CREATE TABLE IF NOT EXISTS` statements in `Program.cs` (PostgreSQL dialect). To change schema, edit both the EF model (`AppDbContext.OnModelCreating`) and the raw SQL in `EnsureTablesExistAsync`.
- Seed data (`SeedData.cs`) inserts 13 restaurants (U Alexa first, with a Website) and menus **for today's date only**. The API filters by `?date=`, so menus exist only for the current day unless added manually.
- `Meal.Price` is `decimal` in EF and `numeric(8,2)` in the raw PostgreSQL DDL — consistent on both sides.

## Script (`script/`)

- Uses the Open WebUI API at `https://llm.ai.e-infra.cz/v1/` (OpenAI-compatible) with model `qwen3.5` — the model is multimodal, so photo-based menus are supported.
- Requires an API key in `script/.env` (`api_key=...`), generated in Open WebUI under Settings → Account → API keys. The `.env` file is gitignored.
- Reads restaurant ID 1 from the same PostgreSQL database as the backend. Connection can be overridden with `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (environment variables or `.env`); defaults match `appsettings.json` (`localhost:5432/zvolenmenu`, user `postgres`). Sends page text plus up to 5 images to the API for parsing. Does not write to the DB.
- Setup: `python3 -m venv .venv` in `script/`, then `pip install -r requirements.txt`.

## Frontend TypeScript strictness

`tsconfig.app.json` enables flags that catch patterns common in other React codebases:

- `erasableSyntaxOnly` — no enums, no parameter properties, no namespaces with runtime code.
- `verbatimModuleSyntax` — use `import type` for type-only imports.
- `noUnusedLocals` / `noUnusedParameters` — remove unused declarations.

## Verification

```bash
# Frontend
cd frontend && npm run lint && npm run build

# Backend
cd backend/src/ZvolenMenu.Api && dotnet build
```

No test suites exist; verification is lint + build.
