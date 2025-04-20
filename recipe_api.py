import os
import openai
from base64 import b64encode
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ── 1. Konfiguration ──────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Strukturerad Recept‑generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ── 2. Hälsokoll ──────────────────────────────────────────────────────────
@app.api_route("/", methods=["GET", "HEAD"])
async def root(request: Request):
    if request.method == "HEAD":
        return JSONResponse(content=None, status_code=200)
    return {"status": "ok"}

# ── 3. /generate ──────────────────────────────────────────────────────────
@app.post("/generate")
async def generate(
    choice: str = Form(...),
    difficulty: str = Form(...),
    meal_type: str = Form(...),
    num_people: str = Form(...),
    cuisine_pref: str = Form(""),
    dietary_pref: str = Form(""),
    textfile: UploadFile | None = File(None),
    image: UploadFile | None = File(None),
):
    varulista = ""

    if choice == "1":
        if not textfile:
            raise HTTPException(400, "textfile saknas")
        varulista = (await textfile.read()).decode("utf-8")

    elif choice == "2":
        if not image:
            raise HTTPException(400, "image saknas")
        img64 = b64encode(await image.read()).decode()
        vision_prompt = [
            {"type": "text",
             "text": ("Detta är en bild av mitt kylskåp. "
                      "Lista alla ingredienser på svenska, en per rad.")},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{img64}"}}
        ]
        rsp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": vision_prompt}]
        )
        varulista = rsp.choices[0].message.content

    elif choice == "3":
        if not textfile:
            raise HTTPException(400, "textfile saknas")
        varulista = (await textfile.read()).decode("utf-8")

    else:
        raise HTTPException(400, "ogiltigt choice‑värde")

    prompt = f"""
Nedan finns en lista över tillgängliga varor. Skriv ett recept med fokus på "Longevity":
- Svårighetsgrad: {difficulty}
- Måltid: {meal_type}
- Antal personer: {num_people}
- Kök: {cuisine_pref or 'valfritt'}
- Kostpreferens: {dietary_pref or 'ingen'}

Strukturera ditt svar i JSON-format med fälten:
- "titel": Namn på rätten
- "instruktioner": Steg för steg-instruktioner
- "ingredienser": Lista på ingredienser du har
- "eventuellt_saknas": Lista på ingredienser som eventuellt saknas
- "longevity_fordelar": Fördelar med avseende på Longevity

Lista över varor:
{varulista}
""".strip()

    chat = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    usage = chat.usage
    print(f"Prompt: {usage.prompt_tokens}  Completion: {usage.completion_tokens}  Total: {usage.total_tokens}")

    recipe_json = chat.choices[0].message.content

    return JSONResponse(content={"recipe": recipe_json})
