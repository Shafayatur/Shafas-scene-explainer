import streamlit as st
import requests
from PIL import Image, ImageDraw
import os
import time
from dotenv import load_dotenv
from groq import Groq

# 🔐 Load environment variables
load_dotenv()

KEY = os.getenv("AZURE_KEY")
ENDPOINT = os.getenv("AZURE_ENDPOINT")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Try to import Ollama (local only)
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Initialize Groq client (cloud fallback)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

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
def build_prompt(caption, objects, text, question):
    return f"""You are an AI assistant analyzing an image. Here's what you know about the image:

Scene Description: {caption}
Detected Objects: {", ".join(objects) if objects else "none"}
Detected Text: {", ".join(text) if text else "none"}

Question: {question}

Please provide a clear, concise answer based on the information above."""


# 🤖 LLM Function with Fallback (Ollama → Groq)
def ask_llm(prompt_data, question):
    full_prompt = build_prompt(prompt_data['caption'], prompt_data['objects'], prompt_data['text'], question)
    
    # Try Ollama first (local)
    if OLLAMA_AVAILABLE:
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that analyzes image descriptions and answers questions about them."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )
            return response['message']['content'], "Ollama (local)"
        except Exception as e:
            st.warning(f"Ollama failed: {str(e)}. Falling back to Groq...")
    
    # Fallback to Groq (cloud)
    if groq_client:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that analyzes image descriptions and answers questions about them."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=500
            )
            return chat_completion.choices[0].message.content, "Groq (cloud)"
        except Exception as e:
            return f"Error: {str(e)}", "None"
    else:
        return "No LLM available. Please install Ollama locally or set GROQ_API_KEY.", "None"


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

    # 🤖 LLM with fallback
    answer = None
    llm_source = None
    if user_question:
        with st.spinner("Thinking..."):
            answer, llm_source = ask_llm({
                'caption': caption_text,
                'objects': unique_objects,
                'text': text_output
            }, user_question)

    # 🎨 UI
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.image(image, use_column_width=True)

    with col2:
        st.subheader("Quick Summary")
        st.write(caption_text)
        if llm_source:
            st.caption(f"🤖 Using: {llm_source}")

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