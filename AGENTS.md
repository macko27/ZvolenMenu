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

- SQLite file at `backend/data/zvolenmenu.db`, gitignored, auto-created on first run.
- **No EF migrations.** Schema is created at startup via `EnsureCreatedAsync` plus manual `CREATE TABLE IF NOT EXISTS` statements in `Program.cs`. To change schema, edit both the EF model (`AppDbContext.OnModelCreating`) and the raw SQL in `EnsureTablesExistAsync`.
- Seed data (`SeedData.cs`) inserts 12 restaurants and menus **for today's date only**. The API filters by `?date=`, so menus exist only for the current day unless added manually.
- `Meal.Price` is `decimal` in EF but `TEXT` in the raw SQLite DDL — a known mismatch, not a bug to "fix" casually.

## Script (`script/`)

- Uses **Ollama** at `http://localhost:11434` with model `qwen2.5:7b` — the README's Gemini/Google AI Studio instructions are stale; trust `main.py`.
- Requires Ollama running locally with the model pulled (`ollama pull qwen2.5:7b`).
- Reads restaurant ID 1 from the SQLite DB, scrapes its `Website`, sends page text to Ollama for parsing. Does not write to the DB.
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
