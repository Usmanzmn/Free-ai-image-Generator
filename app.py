from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from io import BytesIO
import base64
import requests
import textwrap

st.set_page_config(page_title="Local AI Image Generator + Text Tool", layout="centered")
st.title("🎨 AI Image Generator & 🖋️ Text Editor (Offline Mode)")

st.markdown("---")

# ------------------------
# PART 1: Image Generation using Local Stable Diffusion API
# ------------------------

st.markdown("## 🧠 Generate Image with Local Stable Diffusion")

prompt = st.text_area("Enter your image prompt", height=80)
generate = st.button("🎨 Generate Image")

generated_image = None

def generate_image_locally(prompt, width=1280, height=720):
    url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": 20,
        "cfg_scale": 7
    }
    try:
        response = requests.post(url, json=payload)
        r = response.json()
        image_data = base64.b64decode(r['images'][0])
        return Image.open(BytesIO(image_data))
    except Exception as e:
        st.error(f"❌ Failed to generate image: {e}")
        return None

if generate and prompt:
    with st.spinner("Generating image..."):
        generated_image = generate_image_locally(prompt)
        if generated_image:
            st.image(generated_image, caption="🖼️ Generated Image", use_column_width=True)

            buffer = BytesIO()
            generated_image.save(buffer, format="JPEG")
            b64 = base64.b64encode(buffer.getvalue()).decode()
            st.markdown(
                f'<a href="data:image/jpeg;base64,{b64}" download="generated.jpg">📥 Download Generated Image (1280x720)</a>',
                unsafe_allow_html=True
            )

# ------------------------
# PART 2: Add Text to Uploaded Image
# ------------------------

st.markdown("---")
st.markdown("## 🖋️ Add Text to an Uploaded Image")

uploaded_img = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"], key="add_text_img")
text_to_add = st.text_area("Enter your custom text here:", height=100)
text_size = st.slider("🔠 Text Size", min_value=10, max_value=100, value=30)
text_color = st.selectbox("🎨 Text Color", ["white", "black", "red", "yellow", "pink"])

font_options = {
    "DejaVu Sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "DejaVu Sans Bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}
font_choice = st.selectbox("🖋️ Font Style", list(font_options.keys()))

def add_text_to_image_centered_custom(img, custom_text, size, font_path, color):
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, size)
    except Exception as e:
        st.error(f"Font load failed: {e}")
        font = ImageFont.load_default()

    max_text_width = img.width - 100  # Leave 50px on each side
    lines = []
    for line in custom_text.split("\n"):
        lines.extend(textwrap.wrap(line, width=40))

    total_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]) + (len(lines) - 1) * 10
    y = img.height // 2 + 40  # Start slightly below center

    for line in lines:
        line_width = font.getbbox(line)[2] - font.getbbox(line)[0]
        x = max((img.width - line_width) // 2, 50)
        draw.text((x, y), line, font=font, fill=color)
        y += font.getbbox(line)[3] + 10

    return img.convert("RGB")

if st.button("🖼️ Add Text to Image"):
    if uploaded_img and text_to_add:
        with st.spinner("Processing image..."):
            image = Image.open(uploaded_img).resize((1280, 720))
            img_with_text = add_text_to_image_centered_custom(
                image, text_to_add, text_size, font_options[font_choice], text_color
            )
            st.image(img_with_text, caption="🖋️ Image with Text", use_column_width=True)

            img_buffer = BytesIO()
            img_with_text.save(img_buffer, format="JPEG")
            b64 = base64.b64encode(img_buffer.getvalue()).decode()
            st.markdown(
                f'<a href="data:image/jpeg;base64,{b64}" download="text_image.jpg">📥 Download Image with Text (1280x720)</a>',
                unsafe_allow_html=True
            )
    else:
        st.warning("⚠️ Please upload an image and enter some text.")
