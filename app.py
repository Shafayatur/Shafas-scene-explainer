import streamlit as st
import requests
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import os
import time

# 🔐 Load environment variables
load_dotenv()

KEY = os.getenv("AZURE_KEY")
ENDPOINT = os.getenv("AZURE_ENDPOINT")
HF_API_KEY = os.getenv("HF_API_KEY")

# 🎯 Streamlit config
st.set_page_config(page_title="Shafa's Scene Explainer")

# 🎯 Title
st.title("Shafa's Scene Explainer")
st.caption("Multimodal Image Understanding System")

# 🔷 SIDEBAR (ONLY INPUTS)
with st.sidebar:
    st.title("Controls")

    search_query = st.text_input("Find object")
    user_question = st.text_input("Ask about image")

    option = st.radio("Input Method", ["Upload", "Camera"])

    if option == "Upload":
        uploaded_file = st.file_uploader("Upload image", type=["jpg", "png", "jpeg"])
        camera_image = None
    else:
        camera_image = st.camera_input("Take photo")
        uploaded_file = None

file = uploaded_file if uploaded_file else camera_image


# 🔍 OCR Function
def extract_text(image_bytes):
    url = ENDPOINT + "vision/v3.2/read/analyze"

    headers = {
        "Ocp-Apim-Subscription-Key": KEY,
        "Content-Type": "application/octet-stream"
    }

    response = requests.post(url, headers=headers, data=image_bytes)
    operation_url = response.headers["Operation-Location"]

    while True:
        result = requests.get(operation_url, headers=headers).json()
        if result["status"] == "succeeded":
            return result
        elif result["status"] == "failed":
            return None
        time.sleep(1)


# 🧠 Prompt Builder
def build_prompt(caption, objects, text):
    return f"""
Scene: {caption}
Objects: {", ".join(objects) if objects else "none"}
Text: {", ".join(text) if text else "none"}

Answer clearly.
"""


# 🤖 HuggingFace LLM
def ask_hf(prompt, question):
    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    payload = {
        "inputs": prompt + "\nQuestion: " + question,
        "parameters": {"max_new_tokens": 100}
    }

    for _ in range(3):
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()

        if isinstance(result, dict) and "error" in result:
            time.sleep(5)
            continue

        try:
            return result[0]["generated_text"]
        except:
            return "Could not generate answer."

    return "Model busy. Try again."


# 🚀 MAIN LOGIC
if file:

    image = Image.open(file)
    image_bytes = file.getvalue()

    # 🌐 Azure Vision
    url = ENDPOINT + "vision/v3.2/analyze"
    params = {"visualFeatures": "Description,Tags,Objects"}

    headers = {
        "Ocp-Apim-Subscription-Key": KEY,
        "Content-Type": "application/octet-stream"
    }

    result = requests.post(url, headers=headers, params=params, data=image_bytes).json()

    objects = result.get("objects", [])

    captions = result.get("description", {}).get("captions", [])
    caption_text = captions[0]["text"] if captions else "No caption"

    # 🎯 Draw boxes
    draw = ImageDraw.Draw(image)
    match_found = False

    for obj in objects:
        rect = obj["rectangle"]
        x, y, w, h = rect["x"], rect["y"], rect["w"], rect["h"]
        label = obj["object"]

        if search_query and search_query.lower() in label.lower():
            color = "green"
            width = 5
            match_found = True
        else:
            color = "red"
            width = 2

        draw.rectangle([x, y, x + w, y + h], outline=color, width=width)
        draw.text((x, y), label, fill=color)

    if search_query:
        st.success(f"Found: {search_query}" if match_found else "Not found")

    # 🔍 OCR
    ocr_result = extract_text(image_bytes)
    text_output = []

    if ocr_result:
        for page in ocr_result["analyzeResult"]["readResults"]:
            for line in page["lines"]:
                text_output.append(line["text"])

    # 🧠 Explanation
    unique_objects = list(set([obj["object"] for obj in objects]))[:4]

    explanation = f"This image shows {caption_text}. "
    if unique_objects:
        explanation += "Objects: " + ", ".join(unique_objects) + ". "
    if text_output:
        explanation += "Text: " + ", ".join(text_output[:3])

    # 🤖 LLM
    answer = None
    if user_question:
        with st.spinner("Thinking..."):
            prompt = build_prompt(caption_text, unique_objects, text_output)
            answer = ask_hf(prompt, user_question)

    # 🎨 UI
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.image(image, use_column_width=True)

    with col2:
        st.subheader("Quick Summary")
        st.write(caption_text)

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Objects", "Text", "Shafa says"])

    with tab1:
        st.write(explanation)

    with tab2:
        for obj in objects:
            st.write(f"{obj['object']} ({round(obj['confidence'],2)})")

    with tab3:
        if text_output:
            st.text_area("", "\n".join(text_output), height=200)
        else:
            st.write("No text found")

    with tab4:
        if answer:
            st.write(answer)
        else:
            st.write("Ask a question from sidebar")