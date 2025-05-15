import streamlit as st
import os
from moviepy.editor import *
from gtts import gTTS
from PIL import Image, ImageColor

st.set_page_config(page_title="30-Second TVC Generator", layout="centered")
st.title("📺 30-Second Commercial Generator")

st.markdown("---")
st.header("🛠️ Input Your Commercial Details")

brand_name = st.text_input("Brand name:")
cta_message = st.text_input("Call-to-action message:", value="Shop now — limited time only!")
offer_message = st.text_input("Offer message:", value="This weekend only – huge savings!")

bg_color = st.color_picker("Background colour", value="#FF0000")

logo_file = st.file_uploader("Upload your brand logo", type=["png", "jpg"])

st.subheader("📦 Product Slots (Up to 3)")
products = []
for i in range(3):
    with st.expander(f"Product {i+1}"):
        name = st.text_input(f"Product {i+1} name:", key=f"name_{i}")
        price = st.text_input(f"Product {i+1} price:", key=f"price_{i}")
        image = st.file_uploader(f"Product {i+1} image:", type=["png", "jpg"], key=f"image_{i}")
        if name and price and image:
            products.append({"name": name, "price": price, "image": image})

if st.button("Generate Commercial"):
    if not brand_name or not logo_file or len(products) == 0:
        st.error("Please provide brand name, logo, and at least one product.")
        st.stop()

    os.makedirs("temp", exist_ok=True)

    logo_path = os.path.join("temp", "logo.png")
    with open(logo_path, "wb") as f:
        f.write(logo_file.read())

    clips = []

    # 0-5s: Brand Intro
    intro_txt = gTTS(text=offer_message, lang='en')
    intro_audio_path = os.path.join("temp", "intro.mp3")
    intro_txt.save(intro_audio_path)
    intro_audio = AudioFileClip(intro_audio_path)

    intro_img = ColorClip(size=(1080, 1920), color=ImageColor.getrgb(bg_color), duration=5)
    intro_logo = ImageClip(logo_path).set_duration(5).resize(height=300).set_position("center")
    intro = CompositeVideoClip([intro_img, intro_logo.set_start(0)], size=(1080, 1920)).set_audio(intro_audio)
    clips.append(intro)

    # 5-20s: Products
    for i, product in enumerate(products):
        duration = 5
        product_audio_path = os.path.join("temp", f"product_{i}.mp3")
        product_txt = gTTS(text=f"{product['name']} for just {product['price']}", lang='en')
        product_txt.save(product_audio_path)
        product_audio = AudioFileClip(product_audio_path)

        product_path = os.path.join("temp", f"product_{i}.png")
        with open(product_path, "wb") as f:
            f.write(product['image'].read())

        product_img = ImageClip(product_path).set_duration(duration).resize(height=800).set_position("center")
        bg = ColorClip(size=(1080, 1920), color=ImageColor.getrgb(bg_color), duration=duration)
        text = TextClip(f"{product['name']}\n{product['price']}", fontsize=60, color='white', method='caption', size=(1000, None)).set_position((40, 1300)).set_duration(duration)
        product_clip = CompositeVideoClip([bg, product_img, text], size=(1080, 1920)).set_audio(product_audio)
        clips.append(product_clip)

    # 20-30s: CTA
    cta_txt = gTTS(text=f"{cta_message} at {brand_name}", lang='en')
    cta_audio_path = os.path.join("temp", "cta.mp3")
    cta_txt.save(cta_audio_path)
    cta_audio = AudioFileClip(cta_audio_path)

    cta_bg = ColorClip(size=(1080, 1920), color=ImageColor.getrgb(bg_color), duration=10)
    cta_logo = ImageClip(logo_path).set_duration(10).resize(height=300).set_position("center")
    cta_text = TextClip(cta_message, fontsize=70, color='white', method='caption', size=(1000, None)).set_position((40, 1400)).set_duration(10)
    cta = CompositeVideoClip([cta_bg, cta_logo, cta_text], size=(1080, 1920)).set_audio(cta_audio)
    clips.append(cta)

    final_video = concatenate_videoclips(clips, method="compose")
    final_path = os.path.join("temp", "commercial.mp4")
    final_video.write_videofile(final_path, fps=24)

    st.video(final_path)
    with open(final_path, "rb") as f:
        st.download_button("📥 Download Commercial", f, file_name="tvc_30s_commercial.mp4")