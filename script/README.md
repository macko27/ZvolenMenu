# Test menu reštaurácie ID 1

Skript načíta iba záznam s `Id = 1`, použije jeho URL zo stĺpca `Website` a
vypíše nájdené menu ako JSON. Do JSON pridá aktuálny dátum a deň v slovenčine.
Databázu nemení.

```powershell
.\script\.venv\Scripts\python.exe -m pip install -r .\script\requirements.txt
.\script\.venv\Scripts\python.exe .\script\main.py
```

Parser používa Gemini Flash cez Google AI Studio. API kľúč nastavte iba v
prostredí, nie do zdrojového kódu:

```powershell
$env:GEMINI_API_KEY = "VÁŠ_API_KĽÚČ"
.\script\.venv\Scripts\python.exe .\script\main.py
```

Skript odošle Google iba text načítanej stránky. Databázu nemení a výsledok
naďalej vypisuje ako JSON.

Stránka U Alexa zverejňuje iba aktuálne menu, nie samostatné menu pre všetky
dni. Skript preto automaticky označí výsledok dnešným dátumom; staršie alebo
budúce menu z tejto URL nie je možné vybrať.
