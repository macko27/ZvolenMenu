"""
Načíta menu reštaurácie s ID 1 pomocou lokálnej Ollamy
a vypíše ho ako JSON.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------
# NASTAVENIE
# ---------------------------------------------------------

DATABASE = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "data"
    / "zvolenmenu.db"
)

RESTAURANT_ID = 1

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"

SLOVAK_DAYS = (
    "pondelok",
    "utorok",
    "streda",
    "štvrtok",
    "piatok",
    "sobota",
    "nedeľa",
)


# ---------------------------------------------------------
# POMOCNÉ FUNKCIE
# ---------------------------------------------------------

def clean(text: str) -> str:
    """Odstráni prebytočné medzery a zalomí text do čitateľnej podoby."""
    return re.sub(r"[ \t]+", " ", text).strip()


# ---------------------------------------------------------
# OLLAMA
# ---------------------------------------------------------

def parse_menu_with_ollama(
    page_text: str,
    menu_date: date,
) -> list[dict[str, object]]:

    day_name = SLOVAK_DAYS[menu_date.weekday()]

    prompt = f"""
Si parser denného menu reštaurácie.

Z textu webovej stránky vyber IBA menu platné pre:

Dátum: {menu_date.isoformat()}
Deň: {day_name}

Stránka môže obsahovať:
- dnešné menu,
- staršie menu,
- menu na ďalšie dni,
- archív,
- navigáciu,
- reklamy,
- kontaktné informácie,
- iný nerelevantný text.

Vyber iba menu platné pre požadovaný dátum.

Vráť VÝHRADNE platný JSON.
Žiadny Markdown.
Žiadne vysvetlenie.

Presný formát:

{{
  "items": [
    {{
      "name": "názov jedla",
      "category": "Polievka",
      "price": 7.20
    }}
  ]
}}

Povolené kategórie:

- Polievka
- Hlavné jedlo
- Šalát
- Dezert

Pravidlá:

1. Zachovaj slovenskú diakritiku.
2. Odstráň gramáže z názvu jedla.
   Napríklad:
   "0,33l Slepačí vývar" -> "Slepačí vývar"
   "150g Kurací rezeň" -> "Kurací rezeň"
3. Odstráň číslovanie na začiatku názvu.
   Napríklad:
   "1. Kurací rezeň" -> "Kurací rezeň"
4. Cenu vráť ako číslo bez znaku €.
5. Ak jednotlivé jedlá nemajú vlastnú cenu, použi cenu celého menu.
6. Nevymýšľaj žiadne jedlá.
7. Nevymýšľaj žiadne ceny.
8. Ak menu pre požadovaný dátum nie je možné jednoznačne identifikovať,
   vráť:
   {{"items": []}}

TEXT WEBOVEJ STRÁNKY:

{page_text}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0,
                },
            },
            timeout=240,
        )

    except requests.ConnectionError as error:
        raise RuntimeError(
            "Nepodarilo sa pripojiť k Ollame. "
            "Skontroluj, či je Ollama spustená."
        ) from error

    except requests.Timeout as error:
        raise RuntimeError(
            "Ollama odpovedala príliš dlho."
        ) from error

    response.raise_for_status()

    data = response.json()

    if "message" not in data:
        raise RuntimeError(
            f"Ollama vrátila neočakávanú odpoveď: {data}"
        )

    text = data["message"].get("content", "").strip()

    if not text:
        raise RuntimeError(
            "Ollama nevrátila žiadny text."
        )

    # Pre prípad, že by model napriek tomu vrátil Markdown.
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    try:
        parsed = json.loads(text)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Ollama nevrátila platný JSON:\n{text}"
        ) from error

    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Ollama vrátila neočakávaný JSON."
        )

    if not isinstance(parsed.get("items"), list):
        raise RuntimeError(
            "Ollama JSON neobsahuje pole 'items'."
        )

    items: list[dict[str, object]] = []

    for item in parsed["items"]:

        if not isinstance(item, dict):
            continue

        name = item.get("name")
        category = item.get("category")
        price = item.get("price")

        if not isinstance(name, str):
            continue

        if not isinstance(category, str):
            continue

        if isinstance(price, (int, float)):
            safe_price = float(price)

        elif price is None:
            safe_price = 0.0

        else:
            continue

        items.append(
            {
                "name": name.strip(),
                "category": category.strip(),
                "price": safe_price,
            }
        )

    return items


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def read_restaurant() -> dict[str, object]:

    if not DATABASE.exists():
        raise RuntimeError(
            f"Databáza neexistuje: {DATABASE}"
        )

    with sqlite3.connect(DATABASE) as connection:

        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT
                Id,
                Name,
                Address,
                Website
            FROM Restaurants
            WHERE Id = ?
            """,
            (RESTAURANT_ID,),
        ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Reštaurácia s ID {RESTAURANT_ID} neexistuje."
        )

    if not row["Website"]:
        raise RuntimeError(
            f"Reštaurácia s ID {RESTAURANT_ID} "
            "nemá vyplnený stĺpec Website."
        )

    return dict(row)


# ---------------------------------------------------------
# SCRAPING
# ---------------------------------------------------------

def read_menu(
    url: str,
    menu_date: date,
) -> list[dict[str, object]]:

    print(
        f"Načítavam stránku: {url}",
        file=sys.stderr,
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/140.0 Safari/537.36"
            ),
            "Accept-Language": "sk-SK,sk;q=0.9",
        },
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # Odstránime veci, ktoré nechceme posielať modelu.
    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
        ]
    ):
        element.decompose()

    page_text = soup.get_text(
        "\n",
        strip=True,
    )

    # Upratanie textu.
    lines = []

    for line in page_text.splitlines():

        line = clean(line)

        if line:
            lines.append(line)

    page_text = "\n".join(lines)

    # Ochrana pred extrémne veľkou stránkou.
    page_text = page_text[:50000]

    print(
        f"Text stránky má {len(page_text)} znakov.",
        file=sys.stderr,
    )

    print(
        "Spracovávam menu cez Ollamu...",
        file=sys.stderr,
    )

    return parse_menu_with_ollama(
        page_text,
        menu_date,
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main() -> int:

    try:

        restaurant = read_restaurant()

        url = str(
            restaurant["Website"]
        )

        menu_date = date.today()

        items = read_menu(
            url,
            menu_date,
        )

        result = {
            "restaurantId": restaurant["Id"],
            "restaurant": restaurant["Name"],
            "address": restaurant["Address"],
            "source": url,
            "menuDate": menu_date.isoformat(),
            "day": SLOVAK_DAYS[
                menu_date.weekday()
            ],
            "items": items,
        }

        sys.stdout.reconfigure(
            encoding="utf-8"
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

        return 0

    except (
        OSError,
        sqlite3.Error,
        requests.RequestException,
        RuntimeError,
        json.JSONDecodeError,
        KeyError,
    ) as error:

        print(
            f"Chyba: {error}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())