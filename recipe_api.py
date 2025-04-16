# recipe_api.py
import os, openai
from fastapi import FastAPI, UploadFile, File, Form
from base64 import b64encode

openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

@app.post("/generate")
async def generate(
    choice: str = Form(...),
    difficulty: str = Form(...),
    meal_type: str = Form(...),
    num_people: str = Form(...),
    cuisine_pref: str = Form(""),
    dietary_pref: str = Form(""),
    textfile: UploadFile | None = File(None),
    image: UploadFile | None = File(None)
):
    # --- läs varulista (samma logik som i ditt skript) ---
    # ... kortad för brevity ...
    prompt = f"...din recept‑prompt med {difficulty} etc..."
    chat = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"recipe": chat.choices[0].message.content}
