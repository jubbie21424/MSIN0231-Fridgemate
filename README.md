# FridgeMate: Your AI Cooking Assistant

A Streamlit-based AI kitchen assistant that helps users turn refrigerator ingredients into recipe suggestions, with optional photo-based ingredient recognition and cuisine filtering for Asian dishes.

## 🚀 Features

- Upload a fridge photo and let GPT-4o-mini recognize ingredients
- Manual ingredient input or combine with auto-detected items
- Choose cooking time, energy level, vibe, budget, and Asian cuisine preferences
- Generate 3 structured recipe options using Groq Llama
- Generate social-media-style recipe imagery using Hugging Face Stable Diffusion
- Save user preferences locally as lightweight session memory

## 🧠 Architecture

The app splits responsibilities across three APIs:

- **OpenAI**: image-based ingredient recognition using GPT-4 Vision (`gpt-4o-mini`)
- **Groq**: structured recipe generation with the Llama 3.3 model
- **Hugging Face**: image generation for finished dish visuals

## 💻 Setup

1. Create a Python virtual environment
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app
   ```bash
   streamlit run mvp.py
   ```

## 🔑 Required API Keys

Enter the following keys in the Streamlit sidebar:

- `Groq API Key`
- `OpenAI API Key`
- `Hugging Face Token`

## 📁 Files

- `mvp.py` — main Streamlit application
- `requirements.txt` — Python dependencies
- `README.md` — project documentation

## ✨ Notes for Portfolio

This project demonstrates:

- Multi-API integration with clear separation of concern
- Image recognition, structured prompt design, and text-to-image generation
- UI-driven product workflow built with Streamlit
- A practical end-to-end AI application suitable for a portfolio demo
