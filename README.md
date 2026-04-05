🧠 Shafa's Scene Explainer
An interactive multimodal AI application that understands and explains images by combining computer vision and language models.
🚀 Overview
Shafa's Scene Explainer is a smart image analysis system that goes beyond basic object detection. It integrates multiple AI capabilities to provide a complete understanding of visual scenes and allows users to interact with the system through natural language queries.
✨ Features
📌 Scene Captioning – Generates a natural description of the image
📦 Object Detection – Detects and highlights objects with bounding boxes
🔍 Object Search – Find specific objects (e.g., "person", "car")
📝 Text Extraction (OCR) – Reads visible text from images
🧠 AI Explanation – Combines all outputs into a human-like summary
💬 Interactive Q&A – Ask questions about the image and get AI responses
📷 Dual Input Support – Upload images or use live camera
🧠 How It Works
The system follows a multimodal pipeline:
Computer Vision (Azure Cognitive Services)
Extracts caption, objects, and text
Context Fusion
Combines visual and textual information
Language Model (HuggingFace)
Generates intelligent responses to user queries
🛠️ Tech Stack
Frontend: Streamlit
Backend: Python
Computer Vision: Azure Cognitive Services
LLM: HuggingFace (FLAN-T5)
Libraries: requests, Pillow
📦 Installation
Clone the repository:
git clone https://github.com/Shafayatur/Shafas-scene-explainer.git
cd Shafas-scene-explainer
Install dependencies:
pip install -r requirements.txt
🔐 Environment Setup
Create a .env file in the root directory:
AZURE_KEY=your_azure_key
AZURE_ENDPOINT=your_endpoint
HF_API_KEY=your_huggingface_token
▶️ Run the App
streamlit run app.py
🌐 Live Demo
(Add your deployed Streamlit link here)
🎯 Use Cases
Visual scene understanding
Accessibility tools for visually impaired users
Smart surveillance systems
AI-powered educational tools
📌 Future Improvements
Confidence-based filtering
Real-time video processing
More advanced LLM integration
Improved UI/UX interactions
👨‍💻 Author
Shafayatur Rahman
📄 License
This project is for educational and demonstration purposes.


