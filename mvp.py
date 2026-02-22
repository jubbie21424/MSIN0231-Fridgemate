import streamlit as st
from google import genai
from google.genai import types
from groq import Groq
import requests
import os
import time

# --- Page Configuration ---
st.set_page_config(page_title="FridgeMate Pro", page_icon="🍳", layout="centered")

# --- 🧠 SMART MEMORY FUNCTIONS ---
def save_feedback(text):
    """Appends user preferences to a local file to simulate persistent AI learning."""
    with open("memory.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

def load_trimmed_memory(limit=5):
    """Loads the most recent interactions to keep the AI's context window relevant."""
    if os.path.exists("memory.txt"):
        with open("memory.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            return lines[-limit:]
    return []

# --- Sidebar: System Configuration & Memory Display ---
with st.sidebar:
    st.title("⚙️ System Settings")
    provider = st.radio("Select AI Provider", ["Gemini (Google)", "Groq (Llama)"])
    
    if provider == "Gemini (Google)":
        api_key = st.text_input("Gemini API Key", type="password")
        model_id = "gemini-2.0-flash"
    else:
        api_key = st.text_input("Groq API Key", type="password")
        model_id = "llama-3.3-70b-versatile"
    
    st.divider()
    # Required for the 2026 Router Image Generation API
    hf_token = st.text_input("Hugging Face Token", type="password", help="Get your free token at hf.co/settings/tokens")
    
    st.divider()
    st.header("🧠 Active Session Memory")
    active_memories = load_trimmed_memory()
    if active_memories:
        st.write("Current AI Preferences:")
        for pref in active_memories:
            st.caption(f"• {pref}")
        
        if st.button("Reset AI Memory"):
            if os.path.exists("memory.txt"): os.remove("memory.txt")
            st.success("Memory cleared!")
            st.rerun()
    else:
        st.write("AI is currently a blank slate.")

# --- 🎨 AI Image Generation Logic (Multi-Modal Layer) ---
def generate_hf_image(prompt, token):
    """
    Connects to the 2026 Hugging Face Router API.
    Handles 503 Service Unavailable errors by waiting for the model to load.
    """
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {token}"}
    
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=60)
            if response.status_code == 200:
                return response.content
            elif response.status_code == 503:
                # Model is still waking up from sleep mode
                wait_time = response.json().get("estimated_time", 20)
                st.info(f"⏳ AI Artist is waking up... Waiting {int(wait_time)}s.")
                time.sleep(wait_time)
            else:
                return None
        except Exception:
            return None
    return None

# --- Main UI ---
st.title("🍳 FridgeMate")
st.markdown("*Reducing decision fatigue with professional culinary AI.*")
st.divider()

# --- INPUT FLOW: Gather Context ---
st.markdown("#### 1. Inventory & Context")
ingredients = st.text_area("What's in your fridge?", placeholder="e.g., 2 eggs, kimchi, chicken breast", height=100)

c1, c2, c3 = st.columns(3)
with c1:
    time_avail = st.select_slider("Time", options=["15min", "30min", "1hr+"])
with c2:
    energy_level = st.select_slider("Energy", options=["Low", "Medium", "High"])
with c3:
    vibe = st.text_input("Vibe", placeholder="e.g., Spicy comfort")

col_a, col_b = st.columns(2)
with col_a:
    budget = st.text_input("Extra Budget", placeholder="e.g., £5")
with col_b:
    grocery_access = st.selectbox("Asian Grocery Access", ["Limited", "Occasional", "Frequent"])

# --- Action Button: Triggers Decision Engine ---
if st.button("Decide for Me (Generate 3 Options)", use_container_width=True, type="primary"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar!")
    else:
        with st.spinner("AI is calculating portions and creative recipes..."):
            try:
                # Inject persistent memory into the system prompt
                recent_mem = ". ".join(load_trimmed_memory())
                
                # Instruction to the LLM to maintain a strict parsable structure
                sys_instruct = f"""
                You are FridgeMate, a precise professional chef AI. History: {recent_mem}. 
                Provide exactly 3 distinct meal options based on user inventory.
                
                For each option:
                - RECIPE: Include EXACT measurements (e.g., 200ml water, 1 tbsp salt) and numbered steps.
                - LEVEL: Specify difficulty (Easy/Medium/Hard) and a brief technical reason.
                - COST: Provide estimated extra cost in GBP £.
                - CAPTION: An engaging social media post with emojis and hashtags.
                
                Structure (MUST use '---' as delimiter):
                ---
                NAME: [Dish Name]
                TIME: [Prep Time]
                LEVEL: [Level + Reason]
                SHOPPING: [Missing items to buy]
                COST: £[Amount]
                IMG_KEY: [Food noun for image prompt]
                ING_KEY: [Main raw ingredient for image prompt]
                RECIPE: [Ingredients with amounts, followed by numbered steps]
                CAPTION: [Instagram style text]
                ---
                """
                prompt_text = f"Inventory: {ingredients}, Time: {time_avail}, Vibe: {vibe}, Budget: {budget}"

                if provider == "Gemini (Google)":
                    client = genai.Client(api_key=api_key)
                    res = client.models.generate_content(model=model_id, 
                        config=types.GenerateContentConfig(system_instruction=sys_instruct),
                        contents=prompt_text)
                    st.session_state.last_options = res.text
                else:
                    client = Groq(api_key=api_key)
                    res = client.chat.completions.create(model=model_id,
                        messages=[{"role": "system", "content": sys_instruct}, {"role": "user", "content": prompt_text}])
                    st.session_state.last_options = res.choices[0].message.content
                st.rerun()
            except Exception as e:
                st.error(f"Logic Error: {e}")

# --- OUTPUT DELIVERY: Parsing & Multi-Modal Display ---
if "last_options" in st.session_state:
    st.markdown("### ✨ Your 3 Matches")
    raw_options = st.session_state.last_options.split("---")
    
    idx = 0
    for opt in raw_options:
        if "NAME:" in opt:
            with st.container(border=True):
                lines = opt.strip().split('\n')
                def get_val(label):
                    for l in lines:
                        if label in l: return l.replace(label, "").strip()
                    return "N/A"

                st.subheader(f"Option {idx+1}: {get_val('NAME:')}")
                
                # Grid for Metadata
                m1, m2 = st.columns(2)
                m1.write(f"⏱️ **Prep Time:** {get_val('TIME:')}")
                m2.write(f"🔥 **Difficulty:** {get_l('LEVEL:') if 'get_l' in locals() else get_val('LEVEL:')}")
                
                m3, m4 = st.columns(2)
                m3.write(f"🛒 **To Buy:** {get_val('SHOPPING:')}")
                m4.write(f"💰 **Estimated Cost:** {get_val('COST:')}")

                # Detailed Recipe (Measurements + Steps)
                with st.expander("📖 View Precise Recipe & Instructions"):
                    if "RECIPE:" in opt:
                        # Extract recipe block between tags
                        recipe_content = opt.split("RECIPE:")[1].split("CAPTION:")[0].strip()
                        st.markdown(recipe_content)

                # --- 🎨 Generate Dual-Image Visual Plog ---
                if st.button(f"🎨 Generate Plog & Caption ({get_val('NAME:')})", key=f"btn_{idx}"):
                    if not hf_token:
                        st.warning("Please provide a Hugging Face Token in the sidebar.")
                    else:
                        with st.spinner("Visualizing your meal via Stable Diffusion XL..."):
                            # Image 1: Finished Dish
                            p_done = f"Professional food photography, plated {get_val('NAME:')}, {get_val('IMG_KEY:')}, cinematic lighting, 8k"
                            img_done = generate_hf_image(p_done, hf_token)
                            
                            # Image 2: Raw Ingredients
                            p_raw = f"Aesthetic kitchen flatlay, {get_val('ING_KEY:')}, raw ingredients on rustic wood, 8k"
                            img_raw = generate_hf_image(p_raw, hf_token)

                            if img_done and img_raw:
                                col_a, col_b = st.columns(2)
                                with col_a: st.image(img_raw, caption="📸 The Prep")
                                with col_b: st.image(img_done, caption="📸 The Result")
                                
                                # Display AI Generated Social Caption
                                st.success("📝 **Recommended Social Media Caption:**")
                                st.write(get_val("CAPTION:"))
                                
                                # Enable download of the result image
                                st.download_button("💾 Download Dish Image", data=img_done, file_name=f"{get_val('NAME:')}.jpg", key=f"dl_{idx}")
                            else:
                                st.error("Image API is currently busy. Please try again.")
                idx += 1

# --- FEEDBACK LOOP: The Teaching Mechanism ---
st.divider()
st.subheader("📝 Feedback & Learning")
st.write("Help FridgeMate adapt to your taste (e.g., 'I dislike cilantro', 'Make it spicier').")
user_pref = st.text_input("Enter a new preference:", placeholder="e.g., I have a nut allergy...")

if st.button("Submit & Teach AI"):
    if user_pref:
        save_feedback(user_pref)
        st.success("Preference saved! AI memory updated.")
        st.rerun()

st.divider()
st.caption("FridgeMate Precise v2.0 | Optimized for UCL MSIN0231 Showcase | 2026 API Compliant")
