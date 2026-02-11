import os, io, base64
import requests
import streamlit as st
from PIL import Image as PILImage, ImageOps
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
import json
from google.oauth2 import service_account




# --- CONFIG ---
PROJECT_ID = "fashion-app-487018"
LOCATION = "us-central1"

st.set_page_config(page_title="AI Fashion Lab - Try-On", layout="wide")
st.title("👕 AI Fashion Lab — Virtual Try-On")


# ---------- Helpers ----------
def normalize_photo(img: PILImage.Image, target_h: int = 1280) -> PILImage.Image:
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    if h > target_h:
        new_w = int(w * target_h / h)
        img = img.resize((new_w, target_h))
    return img

def pil_to_b64(pil_img: PILImage.Image) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# Quitar fondo (opcional)
def remove_bg_if_available(product_img: PILImage.Image) -> PILImage.Image:
    try:
        from rembg import remove
        out = remove(product_img.convert("RGBA"))
        return out.convert("RGBA")
    except Exception:
        return product_img.convert("RGBA")

def virtual_try_on(person_img: PILImage.Image, product_img: PILImage.Image):
    # Siempre 1 resultado
    sample_count = 1

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

    creds.refresh(GoogleAuthRequest())
    token = creds.token

    person_b64 = pil_to_b64(person_img.convert("RGB"))
    product_b64 = pil_to_b64(product_img.convert("RGBA"))

    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
        f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/"
        f"models/virtual-try-on-001:predict"
    )

    body = {
        "instances": [
            {
                "personImage": {"image": {"bytesBase64Encoded": person_b64}},
                "productImages": [{"image": {"bytesBase64Encoded": product_b64}}],
            }
        ],
        "parameters": {"sampleCount": sample_count},
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=body, timeout=180)

    if not r.ok:
        raise RuntimeError(f"{r.status_code} {r.text}")

    pred = r.json()["predictions"][0]
    out_bytes = base64.b64decode(pred["bytesBase64Encoded"])
    return PILImage.open(io.BytesIO(out_bytes)).convert("RGB")


# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("Configuración")

    uploaded_person = st.file_uploader("📸 Foto de la persona", type=["jpg", "jpeg", "png"])
    uploaded_product = st.file_uploader("👕 Foto de la prenda (producto)", type=["jpg", "jpeg", "png"])

    st.divider()

    clean_product = st.checkbox("✨ Quitar fondo a la prenda (recomendado)", value=True)

    st.divider()

    # ---- UX TIPS ----
    st.info("""
💡 **Cómo conseguir resultados MÁS realistas**

• Usa una **prenda con fondo blanco o transparente**  
• Evita fotos con **maniquí o cuerpo** en la imagen  
• La prenda debería estar **estirada y centrada**  
• Activa *Quitar fondo* si la foto no es limpia
""")


# ---------- MAIN ----------
st.markdown("""
#### 🧵 Tips rápidos para un Try-On perfecto

✅Fondo sin ruido o elementos distractores🚫Sin maniquí ni cuerpo en la foto del producto📏Prenda estirada y centrada✨Usa *Quitar fondo* si la foto es casual
""")

if not uploaded_person or not uploaded_product:
    st.info("Sube una foto de la persona y una foto de la prenda para probar el Virtual Try-On 🙂")
    st.stop()

person_img = normalize_photo(PILImage.open(uploaded_person))
product_img = PILImage.open(uploaded_product)

if clean_product:
    product_img = remove_bg_if_available(product_img)
else:
    product_img = product_img.convert("RGBA")

col1, col2 = st.columns(2)
with col1:
    st.image(person_img, caption="Persona", use_container_width=True)
with col2:
    st.image(product_img, caption="Prenda subida", use_container_width=True)

if st.button("👕 Probar prenda"):
    with st.spinner("Probando la prenda..."):
        try:
            out = virtual_try_on(person_img, product_img)

            st.success("✨ ¡Listo!")

            # Resultado más pequeño y centrado
            colA, colB, colC = st.columns([1, 2, 1])
            with colB:
                st.image(out, caption="Resultado", width=500) 

        except Exception as e:
            st.error(f"Error técnico: {e}")
            st.info("Si ves 403 → permisos. 404 → modelo/región. 400 → formato de imagen.")
