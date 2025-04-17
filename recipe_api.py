# recipe_api.py
import os, openai
from base64 import b64encode

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# ── 1. Konfiguration ──────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")   # sätts i Render‑Environment

app = FastAPI(title="Recept‑generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 2. Root = HTML‑formulär (GET) + hälsokoll (HEAD) ──────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_get():
    return """
    <!DOCTYPE html>
    <html lang="sv">
      <head>
        <meta charset="utf-8" />
        <title>Generera Longevity‑recept</title>
        <style>
          body{font-family:sans-serif;max-width:600px;margin:40px auto}
          input,select,textarea{width:100%;padding:8px;margin:6px 0}
          button{background:#16a34a;color:#fff;padding:10px 16px;border:0;border-radius:4px}
        </style>
      </head>
      <body>
        <h1>Generera Longevity‑recept</h1>
        <form method="post" action="/generate">
          <label>Datakälla</label>
          <select name="choice">
            <option value="1">Inventarielista (klistra in text)</option>
            <option value="3">Befintlig inventarielista (klistra in text)</option>
          </select>

          <textarea name="invent_text" rows="4" placeholder="Klistra in varulista här (en rad per vara)"></textarea>

          <input name="difficulty"   placeholder="Svårighetsgrad" required />
          <input name="meal_type"    placeholder="Måltid"          required />
          <input name="num_people"   placeholder="Antal personer"  required />
          <input name="cuisine_pref" placeholder="Kök (valfritt)"  />
          <input name="dietary_pref" placeholder="Kost (valfritt)" />

          <button type="submit">Generera recept</button>
        </form>
      </body>
    </html>
    """

@app.head("/", include_in_schema=False)
async def root_head():
    return PlainTextResponse(status_code=200)

# ── 3. /generate  ─────────────────────────────────────────────────────────
@app.post("/generate")
async def generate(
    choice: str            = Form(...),         # "1" eller "3"
    difficulty: str        = Form(...),
    meal_type: str         = Form(...),
    num_people: str        = Form(...),
    cuisine_pref: str      = Form(""),
    dietary_pref: str      = Form(""),
    invent_text: str       = Form(""),          # text från formuläret
):
    # 3.1  Hämta varulistan
    if choice not in ("1", "3") or not invent_text.strip():
        raise HTTPException(400, "Ingen varulista inskickad")

    varulista = invent_text.strip()

    # 3.2  Bygg prompten
    prompt = f"""
Nedan finns en lista över tillgängliga varor. Skriv ett recept med fokus på "Longevity":
- Svårighetsgrad: {difficulty}
- Måltid: {meal_type}
- Antal personer: {num_people}
- Kök: {cuisine_pref or 'valfritt'}
- Kostpreferens: {dietary_pref or 'ingen'}

Strukturera svaret enligt:

1) Förslag på rätt
2) Gör såhär
3) Ingredienser du har
4) Har du?
5) Longevity‑fördelar

Lista över varor:
{varulista}
    """.strip()

    # 3.3  Anropa ChatGPT
    chat = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    usage = chat.usage
    print(f"Prompt: {usage.prompt_tokens}  Completion: {usage.completion_tokens}  Total: {usage.total_tokens}")

    # 3.4  Returnera receptet
    return JSONResponse({"recipe": chat.choices[0].message.content})
