import streamlit as st
import requests
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from io import BytesIO
import zipfile
import base64
import textwrap

# -----------------------------
# Config and Branding
# -----------------------------
st.set_page_config(
    page_title="PixelGenius - AI Image Generator",
    page_icon="🎨",
    layout="wide"
)

try:
    st.image("assets/logo.png", width=140)
except Exception:
    st.warning("⚠️ Logo image failed to load.")

st.title("🎨 PixelGenius: AI Image Generator")
st.caption("Create high-quality images using Hugging Face Stable Diffusion XL (Free API) with real-time filters and styles.")
st.divider()

# -----------------------------
# Load API Token from Streamlit Secrets
# -----------------------------
try:
    api_token = st.secrets["HUGGINGFACE_TOKEN"]
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    HEADERS = {"Authorization": f"Bearer {api_token}"}
except KeyError:
    st.error("🔴 API Token not found! Did you add it to Streamlit Secrets?")
    st.stop()

# -----------------------------
# Utility Functions
# -----------------------------
def generate_image(prompt):
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        st.error(f"❌ API Error {response.status_code}: {response.text}")
        return None

def apply_filters(img, brightness, contrast, sharpness):
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img

def get_image_download_link(img_list):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for idx, (caption, img) in enumerate(img_list):
            img_buffer = BytesIO()
            img.save(img_buffer, format="PNG")
            zip_file.writestr(f"{caption.replace(' ', '_')}.png", img_buffer.getvalue())
    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="pixelgenius_images.zip">⬇️ Download All Images (ZIP)</a>'
    return href

# -----------------------------
# Generator UI
# -----------------------------
st.sidebar.header("🧠 Generator Controls")
style_options = ["Realistic", "Anime", "Sketch", "Cyberpunk", "All Styles"]
style = st.sidebar.selectbox("🎨 Choose Style", style_options)
num_images = st.sidebar.slider("🖼️ Number of Images", 1, 2, 1)

st.sidebar.markdown("### 🎛️ Filters")
brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0)
contrast = st.sidebar.slider("Contrast", 0.5, 2.0, 1.0)
sharpness = st.sidebar.slider("Sharpness", 0.5, 2.0, 1.0)

st.markdown("### ✏️ Enter your prompt")
prompt = st.text_input("For example: *A futuristic city at sunset, in anime style*")

if prompt:
    if st.button("🚀 Generate Images"):
        selected_styles = [style] if style != "All Styles" else ["Realistic", "Anime", "Sketch", "Cyberpunk"]
        total_images = len(selected_styles) * num_images
        st.info(f"Generating {total_images} image(s) with style(s): {', '.join(selected_styles)}")

        history = st.session_state.get("prompt_history", [])
        history.append(prompt)
        st.session_state.prompt_history = history

        images = []
        with st.spinner("Generating..."):
            for s in selected_styles:
                for i in range(num_images):
                    img = generate_image(f"{s} style - {prompt}")
                    if img:
                        filtered_img = apply_filters(img, brightness, contrast, sharpness)
                        images.append((f"{s} Image {i+1}", filtered_img))

        st.success("✅ Done!")

        if images:
            cols = st.columns(min(4, len(images)))
            for i, (caption, img) in enumerate(images):
                with cols[i % len(cols)]:
                    st.image(img.resize((640, 360)), caption=caption, use_column_width=False)
            st.markdown(get_image_download_link(images), unsafe_allow_html=True)
        else:
            st.warning("⚠️ No images were generated. Try another prompt or check API status.")

        st.divider()
        st.markdown("### 🕘 Prompt History")
        for i, p in enumerate(reversed(history[-5:]), 1):
            st.markdown(f"{i}. _{p}_")
else:
    st.info("👈 Enter a prompt above to start generating images.")

# -----------------------------
# Text on Uploaded Image
# -----------------------------
st.divider()
st.markdown("### 🖋️ Add Text to an Uploaded Image")

uploaded_img = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"], key="add_text_img")
text_to_add = st.text_area("Enter your custom text here:", height=100)
text_size = st.slider("🔠 Text Size", min_value=10, max_value=100, value=30)

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def add_text_to_image_centered_custom(img, custom_text, size, font_path):
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, size)
    except Exception as e:
        st.error(f"Font load failed: {e}")
        font = ImageFont.load_default()

    width, height = img.size
    padding = 50  # 50px left and right
    max_text_width = width - (2 * padding)

    # Wrap text manually based on visual width
    lines = []
    for paragraph in custom_text.split("\n"):
        current_line = ""
        for word in paragraph.split():
            test_line = f"{current_line} {word}".strip()
            if font.getlength(test_line) <= max_text_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

    line_height = font.getbbox("A")[3] - font.getbbox("A")[1] + 10
    total_text_height = len(lines) * line_height
    start_y = height // 2 + (height // 4 - total_text_height // 2)  # Bottom half centered

    for line in lines:
        text_width = font.getlength(line)
        x = (width - text_width) // 2
        draw.text((x, start_y), line, font=font, fill="white")
        start_y += line_height

    return img.convert("RGB")
