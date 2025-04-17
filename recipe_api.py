# recipe_api.py
import os
import openai
from base64 import b64encode

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# ── 1. Konfiguration ──────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")  # sätts i Render‑Environment

app = FastAPI(title="Recept‑generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 2. Hälsokoll så Render & Shopify får 200 OK ───────────────────────────
@app.get("/", include_in_schema=False)
async def root_get():
    return {"status": "ok"}

@app.head("/", include_in_schema=False)
async def root_head():
    return PlainTextResponse(status_code=200)

# (valfritt) GET på proxy‑stigen – bra som enkel test
@app.get("/generate", include_in_schema=False)
async def generate_get():
    return PlainTextResponse("Recept‑generatorn är igång ✓")


# ── 3. POST /generate  ────────────────────────────────────────────────────
@app.post("/generate")
async def generate(
    choice: str            = Form(...),  # "1", "2" eller "3"
    difficulty: str        = Form(...),
    meal_type: str         = Form(...),
    num_people: str        = Form(...),
    cuisine_pref: str      = Form(""),
    dietary_pref: str      = Form(""),
    textfile: UploadFile | None = File(None),
    image:    UploadFile | None = File(None),
):
    # 3.1 Hämta varulistan beroende på val
    varulista = ""

    if choice == "1":  # Inventarielista .txt
        if not textfile:
            raise HTTPException(400, "textfile saknas")
        varulista = (await textfile.read()).decode("utf‑8")

    elif choice == "2":  # Bild på kylskåpet
        if not image:
            raise HTTPException(400, "image saknas")
        img64 = b64encode(await image.read()).decode()
        vision_prompt = [
            {"type": "text",
             "text": ("Detta är en bild av mitt kylskåp. "
                      "Lista alla ingredienser på svenska, en per rad.")},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{img64}"}},
        ]
        rsp = openai.ChatCompletion.create(  # openai 0.28‑API
            model="gpt-4o",
            messages=[{"role": "user", "content": vision_prompt}],
        )
        varulista = rsp.choices[0].message.content

    elif choice == "3":  # Befintlig inventarielista .txt
        if not textfile:
            raise HTTPException(400, "textfile saknas")
        varulista = (await textfile.read()).decode("utf‑8")

    else:
        raise HTTPException(400, "ogiltigt choice‑värde")

    # 3.2 Bygg huvud‑prompten
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

    # 3.3 Anropa ChatGPT
    chat = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
    )

    # 3.4 Logga token‑åtgång
    usage = chat.usage
    print(
        f"Prompt: {usage.prompt_tokens}  "
        f"Completion: {usage.completion_tokens}  "
        f"Total: {usage.total_tokens}"
    )

    # 3.5 Returnera receptet
    return JSONResponse({"recipe": chat.choices[0].message.content})
