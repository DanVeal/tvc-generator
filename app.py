import streamlit as st
import os
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import uuid
import subprocess

st.set_page_config(page_title="30s TVC Generator (No MoviePy)", layout="centered")
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
    job_id = str(uuid.uuid4())
    job_dir = os.path.join("temp", job_id)
    os.makedirs(job_dir)

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    image_size = (1080, 1920)

    def make_slide(text_lines, image_path=None, output_image="frame.png"):
        img = Image.new("RGB", image_size, color=bg_color)
        draw = ImageDraw.Draw(img)

        # Add text
        font = ImageFont.truetype(font_path, 60)
        y_text = 1500
        for line in text_lines:
            w, h = draw.textsize(line, font=font)
            draw.text(((image_size[0]-w)/2, y_text), line, font=font, fill="white")
            y_text += h + 20

        if image_path:
            product_img = Image.open(image_path).convert("RGBA")
            product_img.thumbnail((1000, 1000))
            x = (image_size[0] - product_img.width) // 2
            y = 400
            img.paste(product_img, (x, y), product_img if product_img.mode == "RGBA" else None)

        out_path = os.path.join(job_dir, output_image)
        img.save(out_path)
        return out_path

    def make_audio(text, filename):
        tts = gTTS(text=text, lang="en")
        path = os.path.join(job_dir, filename)
        tts.save(path)
        return path

    video_parts = []

    # Intro
    logo_path = os.path.join(job_dir, "logo.png")
    with open(logo_path, "wb") as f:
        f.write(logo_file.read())
    intro_img = make_slide([offer_message], logo_path, "frame0.png")
    intro_audio = make_audio(offer_message, "audio0.mp3")
    video_parts.append((intro_img, intro_audio, 5))

    # Products
    for i, product in enumerate(products):
        img_path = os.path.join(job_dir, f"prod_{i}.png")
        with open(img_path, "wb") as f:
            f.write(product["image"].read())
        frame = make_slide([product["name"], product["price"]], img_path, f"frame{i+1}.png")
        audio = make_audio(f"{product['name']} for just {product['price']}", f"audio{i+1}.mp3")
        video_parts.append((frame, audio, 5))

    # CTA
    cta_frame = make_slide([cta_message, f"at {brand_name}"], logo_path, f"frame_final.png")
    cta_audio = make_audio(f"{cta_message} at {brand_name}", f"audio_final.mp3")
    video_parts.append((cta_frame, cta_audio, 10))

    # Generate video segments
    segment_paths = []
    for idx, (img, aud, duration) in enumerate(video_parts):
        segment = os.path.join(job_dir, f"segment_{idx}.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            segment
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        segment_paths.append(segment)

    # Concatenate all segments
    concat_file = os.path.join(job_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for seg in segment_paths:
            f.write(f"file '{seg}'\n")

    final_video = os.path.join(job_dir, "final_video.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", final_video
    ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    st.video(final_video)
    with open(final_video, "rb") as f:
        st.download_button("📥 Download 30s TVC", f, file_name="tvc_commercial.mp4")