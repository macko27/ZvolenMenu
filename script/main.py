"""
Prejde reštaurácie s vyplnenou webovou stránkou z databázy,
pre ktoré ešte nemá uložené dnešné menu. Načíta ich menu
pre celý aktuálny týždeň pomocou API Open WebUI
(https://llm.ai.e-infra.cz) a uloží ho do databázy.
Podporuje aj menu, ktoré je na stránke vo forme obrázka.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urljoin

import psycopg
import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------
# NASTAVENIE
# ---------------------------------------------------------

# PostgreSQL databáza, ktorú používa backend.
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "zvolenmenu"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# Open WebUI API (OpenAI-kompatibilné rozhranie).
API_URL = "https://llm.ai.e-infra.cz/v1/chat/completions"
MODEL = "qwen3.5"

# API kľúč sa načíta zo súboru .env vedľa skriptu.
API_KEY_FILE = Path(__file__).resolve().parent / ".env"

# Obmedzenia pre obrázky, ktoré sa posielajú modelu.
MAX_IMAGES = 5
MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

# Reasoning modely potrebujú dosť priestoru na odpoveď.
MAX_TOKENS = 4000

# qwen3.5 je reasoning model; bez tohto parametra minie všetky tokeny
# na uvažovanie a nevráti žiadny obsah.
CHAT_TEMPLATE_KWARGS = {"enable_thinking": False}

REQUEST_TIMEOUT = 240

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


def load_env() -> dict[str, str]:
    """Načíta hodnoty zo súboru .env vedľa skriptu."""

    values: dict[str, str] = {}

    if not API_KEY_FILE.exists():
        return values

    for line in API_KEY_FILE.read_text(
        encoding="utf-8",
    ).splitlines():

        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and value:
            values[key] = value

    return values


def env_value(
    name: str,
    default: str,
) -> str:
    """Vráti hodnotu z premennej prostredia, prípadne zo súboru .env."""

    value = os.environ.get(name, "").strip()

    if value:
        return value

    return load_env().get(name, "").strip() or default


def load_api_key() -> str:
    """Načíta API kľúč z premennej prostredia 'api_key',
    prípadne zo súboru .env vedľa skriptu."""

    for name in ("api_key", "LLM_API_KEY", "API_KEY"):

        value = env_value(name, "")

        if value:
            return value

    raise RuntimeError(
        "API kľúč nebol nájdený. Nastav premennú prostredia 'api_key' "
        f"alebo pridaj riadok 'api_key=TVOJ_KĽÚČ' do súboru {API_KEY_FILE}."
    )


# ---------------------------------------------------------
# LLM (Open WebUI API)
# ---------------------------------------------------------

def week_bounds(
    menu_date: date,
) -> tuple[date, date]:
    """Vráti pondelok a nedeľu týždňa, do ktorého patrí dátum."""

    monday = menu_date - timedelta(
        days=menu_date.weekday()
    )

    return monday, monday + timedelta(days=6)


def week_dates(menu_date: date) -> list[date]:
    """Vráti zoznam dátumov (pondelok až nedeľa) aktuálneho týždňa."""

    monday, _ = week_bounds(menu_date)

    return [
        monday + timedelta(days=offset)
        for offset in range(7)
    ]


def build_prompt(
    page_text: str,
    menu_date: date,
    image_count: int,
) -> str:

    week_start, week_end = week_bounds(menu_date)

    day_lines = "\n".join(
        f"- {SLOVAK_DAYS[d.weekday()]}: {d.isoformat()}"
        for d in week_dates(menu_date)
    )

    images_note = ""

    if image_count > 0:
        images_note = f"""
Stránka obsahuje aj {image_count} obrázkov, ktoré sú priložené k tejto správe.
Ak je menu uvedené vo forme obrázka (fotografie, plagátu), prečítaj ho
z priložených obrázkov. Iba ak obrázky menu neobsahujú, použi text stránky.
"""

    return f"""
Si parser denného menu reštaurácie.

Z textu webovej stránky vyber IBA menu platné pre aktuálny týždeň:

Od: {week_start.isoformat()}
Do: {week_end.isoformat()}

Dátumy dní v týždni:

{day_lines}
{images_note}
Stránka môže obsahovať:
- menu pre celý aktuálny týždeň,
- menu len pre niektoré dni,
- menu len pre dnešok,
- staršie menu,
- menu na ďalší týždeň,
- archív,
- navigáciu,
- reklamy,
- kontaktné informácie,
- iný nerelevantný text.

Vyber IBA menu platné pre dni aktuálneho týždňa uvedené vyššie.
Menu pre iné dni ignoruj.

Vráť VÝHRADNE platný JSON.
Žiadny Markdown.
Žiadne vysvetlenie.

Presný formát:

{{
  "items": [
    {{
      "date": "2026-09-29",
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

1. "date" je dátum vo formáte YYYY-MM-DD podľa zoznamu
   dní aktuálneho týždňa uvedeného vyššie.
2. Zachovaj slovenskú diakritiku.
3. Odstráň gramáže z názvu jedla.
   Napríklad:
   "0,33l Slepačí vývar" -> "Slepačí vývar"
   "150g Kurací rezeň" -> "Kurací rezeň"
4. Odstráň číslovanie na začiatku názvu.
   Napríklad:
   "1. Kurací rezeň" -> "Kurací rezeň"
5. Cenu vráť ako číslo bez znaku €.
6. Ceny môžu byť rôzne pre rôzne dni týždňa — použi vždy
   cenu platnú pre deň, ku ktorému jedlo patrí.
7. Ak jednotlivé jedlá nemajú vlastnú cenu, použi cenu celého menu
   pre daný deň.
8. Nevymýšľaj žiadne jedlá.
9. Nevymýšľaj žiadne ceny.
10. Nevymýšľaj žiadne dátumy — použi iba dátumy zo zoznamu vyššie.
11. Ak menu pre aktuálny týždeň nie je možné jednoznačne identifikovať,
    vráť:
    {{"items": []}}

TEXT WEBOVEJ STRÁNKY:

{page_text}
"""


def parse_menu_with_llm(
    page_text: str,
    image_parts: list[dict[str, object]],
    menu_date: date,
) -> list[dict[str, object]]:

    prompt = build_prompt(
        page_text,
        menu_date,
        len(image_parts),
    )

    content: list[dict[str, object]] = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    content.extend(image_parts)

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {load_api_key()}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
                "temperature": 0,
                "max_tokens": MAX_TOKENS,
                "stream": False,
                "chat_template_kwargs": CHAT_TEMPLATE_KWARGS,
            },
            timeout=REQUEST_TIMEOUT,
        )

    except requests.ConnectionError as error:
        raise RuntimeError(
            f"Nepodarilo sa pripojiť k API: {API_URL}"
        ) from error

    except requests.Timeout as error:
        raise RuntimeError(
            "API odpovedalo príliš dlho."
        ) from error

    response.raise_for_status()

    data = response.json()

    choices = data.get("choices") or []

    if not choices:
        raise RuntimeError(
            f"API vrátilo neočakávanú odpoveď: {data}"
        )

    message = choices[0].get("message") or {}

    text = (message.get("content") or "").strip()

    if not text:
        raise RuntimeError(
            "Model nevrátil žiadny text. "
            f"Odpoveď API: {data}"
        )

    # Pre prípad, že by model napriek tomu vrátil Markdown
    # alebo blok s uvažovaním.
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL,
    )

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

    text = text.strip()

    try:
        parsed = json.loads(text)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Model nevrátil platný JSON:\n{text}"
        ) from error

    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Model vrátil neočakávaný JSON."
        )

    if not isinstance(parsed.get("items"), list):
        raise RuntimeError(
            "JSON z modelu neobsahuje pole 'items'."
        )

    items: list[dict[str, object]] = []

    allowed_dates = {
        d.isoformat()
        for d in week_dates(menu_date)
    }

    for item in parsed["items"]:

        if not isinstance(item, dict):
            continue

        item_date = item.get("date")
        name = item.get("name")
        category = item.get("category")
        price = item.get("price")

        if not isinstance(item_date, str):
            print(
                "Položka bez dátumu, preskakujem: "
                f"{item}",
                file=sys.stderr,
            )
            continue

        if item_date.strip() not in allowed_dates:
            print(
                f"Položka s dátumom mimo aktuálneho týždňa "
                f"({item_date}), preskakujem: {item}",
                file=sys.stderr,
            )
            continue

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
                "date": item_date.strip(),
                "name": name.strip(),
                "category": category.strip(),
                "price": safe_price,
            }
        )

    return items


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def connect_db() -> psycopg.Connection:
    """Otvorí spojenie s databázou backendu."""

    return psycopg.connect(
        host=env_value("DB_HOST", DB_HOST),
        port=int(env_value("DB_PORT", str(DB_PORT))),
        dbname=env_value("DB_NAME", DB_NAME),
        user=env_value("DB_USER", DB_USER),
        password=env_value("DB_PASSWORD", DB_PASSWORD),
        row_factory=psycopg.rows.dict_row,
    )


def read_restaurants(
    connection: psycopg.Connection,
    menu_date: date,
) -> list[dict[str, object]]:
    """Načíta reštaurácie s webovou stránkou, pre ktoré ešte
    nemáme dnešné menu (aspoň jedno jedlo).

    Reštaurácie s už uloženým dnešným menu preskakuje — ak majú
    týždenné menu, stiahlo sa celé naraz a opakované sťahovanie
    nie je potrebné.
    """

    all_rows = connection.execute(
        """
        SELECT
            "Id",
            "Name",
            "Address",
            "Website"
        FROM "Restaurants"
        WHERE "Website" IS NOT NULL
          AND "Website" <> ''
        ORDER BY "Id"
        """
    ).fetchall()

    if not all_rows:
        raise RuntimeError(
            "V tabuľke Restaurants nie je žiadna reštaurácia "
            "s vyplneným stĺpcom Website."
        )

    covered_ids = {
        int(row["RestaurantId"])
        for row in connection.execute(
            """
            SELECT DISTINCT d."RestaurantId"
            FROM "DailyMenus" d
            JOIN "Meals" m ON m."DailyMenuId" = d."Id"
            WHERE d."MenuDate" = %s
            """,
            (menu_date,),
        ).fetchall()
    }

    restaurants: list[dict[str, object]] = []

    for row in all_rows:

        if int(row["Id"]) in covered_ids:
            print(
                f"Preskakujem {row['Name']} — dnešné menu "
                "už mám uložené.",
                file=sys.stderr,
            )
            continue

        restaurants.append(dict(row))

    return restaurants


def menu_type_id(
    connection: psycopg.Connection,
    category: str,
) -> int:
    """Vráti ID typu menu podľa názvu; neznámy typ vytvorí."""

    connection.execute(
        """
        INSERT INTO "MenuTypes" ("Name")
        VALUES (%s)
        ON CONFLICT ("Name") DO NOTHING
        """,
        (category,),
    )

    row = connection.execute(
        """
        SELECT "Id"
        FROM "MenuTypes"
        WHERE "Name" = %s
        """,
        (category,),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Nepodarilo sa nájsť ani vytvoriť typ menu: {category}"
        )

    return int(row["Id"])


def save_menu_to_db(
    connection: psycopg.Connection,
    restaurant_id: int,
    items: list[dict[str, object]],
) -> None:
    """Uloží denné menu reštaurácie do databázy, rozdelené podľa dátumu.

    Existujúce menu pre daný dátum a reštauráciu je nahradené
    (staré jedlá sa zmažú a vložia sa nové).
    """

    items_by_date: dict[str, list[dict[str, object]]] = {}

    for item in items:
        items_by_date.setdefault(
            str(item["date"]),
            [],
        ).append(item)

    for menu_date_str, date_items in sorted(items_by_date.items()):

        menu_date = date.fromisoformat(menu_date_str)

        row = connection.execute(
            """
            INSERT INTO "DailyMenus" ("RestaurantId", "MenuDate", "Note")
            VALUES (%s, %s, NULL)
            ON CONFLICT ("RestaurantId", "MenuDate") DO UPDATE
            SET "Note" = NULL
            RETURNING "Id"
            """,
            (restaurant_id, menu_date),
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "Nepodarilo sa vložiť denné menu do databázy."
            )

        daily_menu_id = int(row["Id"])

        connection.execute(
            """
            DELETE FROM "Meals"
            WHERE "DailyMenuId" = %s
            """,
            (daily_menu_id,),
        )

        for sort_order, item in enumerate(date_items, start=1):

            type_id = menu_type_id(
                connection,
                str(item["category"]),
            )

            connection.execute(
                """
                INSERT INTO "Meals" (
                    "DailyMenuId",
                    "MenuTypeId",
                    "Name",
                    "Description",
                    "Allergens",
                    "Price",
                    "SortOrder"
                )
                VALUES (%s, %s, %s, NULL, NULL, %s, %s)
                """,
                (
                    daily_menu_id,
                    type_id,
                    str(item["name"]),
                    float(item["price"]),
                    sort_order,
                ),
            )

        print(
            f"Uložené menu pre {menu_date.isoformat()} "
            f"({len(date_items)} jedál).",
            file=sys.stderr,
        )

    connection.commit()


# ---------------------------------------------------------
# SCRAPING
# ---------------------------------------------------------

def collect_image_urls(
    soup: BeautifulSoup,
    page_url: str,
) -> list[str]:
    """Nazbiera URL obrázkov z stránky, ktoré môžu obsahovať menu."""

    urls: list[str] = []

    for image in soup.find_all("img"):

        src = image.get("src")

        if not isinstance(src, str):
            continue

        if not src or src.startswith("data:"):
            continue

        url = urljoin(page_url, src)

        path = url.split("?", 1)[0].lower()

        if not path.endswith(IMAGE_EXTENSIONS):
            continue

        if url not in urls:
            urls.append(url)

        if len(urls) >= MAX_IMAGES:
            break

    return urls


def download_image_as_part(
    url: str,
) -> dict[str, object] | None:
    """Stiahne obrázok a vráti ho ako časť správy pre API."""

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/140.0 Safari/537.36"
                ),
            },
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(
            f"Nepodarilo sa stiahnuť obrázok: {url} ({error})",
            file=sys.stderr,
        )
        return None

    if len(response.content) > MAX_IMAGE_BYTES:
        print(
            f"Obrázok je príliš veľký, preskakujem: {url}",
            file=sys.stderr,
        )
        return None

    mime = response.headers.get(
        "Content-Type",
        "image/jpeg",
    ).split(";", 1)[0].strip()

    if mime not in (
        "image/jpeg",
        "image/png",
        "image/webp",
    ):
        return None

    encoded = base64.b64encode(response.content).decode()

    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime};base64,{encoded}",
        },
    }


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

    # Obrázky si uložíme predtým, než ich zo stránky odstránime.
    image_urls = collect_image_urls(soup, url)

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
        f"Na stránke je {len(image_urls)} obrázkov kandidátov.",
        file=sys.stderr,
    )

    image_parts: list[dict[str, object]] = []

    for image_url in image_urls:

        part = download_image_as_part(image_url)

        if part is not None:
            image_parts.append(part)

    print(
        f"API: {API_URL} (model {MODEL})",
        file=sys.stderr,
    )

    print(
        "Spracovávam menu cez LLM...",
        file=sys.stderr,
    )

    return parse_menu_with_llm(
        page_text,
        image_parts,
        menu_date,
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main() -> int:

    try:

        connection = connect_db()

    except (
        OSError,
        psycopg.Error,
        RuntimeError,
    ) as error:

        print(
            f"Chyba: {error}",
            file=sys.stderr,
        )

        return 1

    try:

        menu_date = date.today()

        restaurants = read_restaurants(
            connection,
            menu_date,
        )

        week_start, week_end = week_bounds(menu_date)

        failed = 0

        sys.stdout.reconfigure(
            encoding="utf-8"
        )

        for restaurant in restaurants:

            restaurant_id = int(
                restaurant["Id"]
            )

            try:

                url = str(
                    restaurant["Website"]
                )

                items = read_menu(
                    url,
                    menu_date,
                )

                save_menu_to_db(
                    connection,
                    restaurant_id,
                    items,
                )

                print(
                    json.dumps(
                        {
                            "restaurantId": restaurant_id,
                            "restaurant": restaurant["Name"],
                            "address": restaurant["Address"],
                            "source": url,
                            "weekStart": week_start.isoformat(),
                            "weekEnd": week_end.isoformat(),
                            "items": items,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )

            except (
                OSError,
                psycopg.Error,
                requests.RequestException,
                RuntimeError,
                json.JSONDecodeError,
                KeyError,
            ) as error:

                connection.rollback()

                failed += 1

                print(
                    f"Chyba pri reštaurácii "
                    f"{restaurant['Name']} "
                    f"(ID {restaurant_id}): {error}",
                    file=sys.stderr,
                )

        if failed:
            print(
                f"Nepodarilo sa spracovať {failed} "
                f"z {len(restaurants)} reštaurácií.",
                file=sys.stderr,
            )
            return 1

        return 0

    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
