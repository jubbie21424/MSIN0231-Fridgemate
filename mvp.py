import streamlit as st
from groq import Groq
import requests
import os
import time
import base64
from openai import OpenAI

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
    st.info("Providers: Groq (Llama 3.3) + OpenAI (GPT-4o Vision)")
    
    # Input for Groq API Key
    api_key = st.text_input("Groq API Key", type="password")
    model_id = "llama-3.3-70b-versatile"
    
    st.divider()
    # OpenAI API Key for Image Recognition
    openai_api_key = st.text_input("OpenAI API Key", type="password", help="Get your key at platform.openai.com/api-keys")
    
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

# --- 🎨 AI Image Generation Logic ---
# --- 🖼️ AI Image Recognition Logic (OpenAI GPT-4o) ---
def recognize_fridge_ingredients(image_data, api_key):
    """
    Uses OpenAI GPT-4o Vision to identify ingredients in a fridge image.
    Returns a comma-separated list of detected ingredients.
    """
    try:
        # Encode image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        client = OpenAI(api_key=api_key)
        
        # Check image size
        image_size_mb = len(image_data) / (1024 * 1024)
        if image_size_mb > 20:
            st.warning(f"⚠️ Image is large ({image_size_mb:.1f}MB). Consider using a smaller file.")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # gpt-4o-mini supports vision and is more affordable
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are a professional chef analyzing a refrigerator photo. Please identify ALL food items and ingredients visible. List them as a comma-separated list with quantities if visible. Format: 'item1 (quantity), item2 (quantity), ...'. Be specific and include: vegetables, proteins, dairy, condiments, frozen items, etc."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3  # Lower temperature for consistent results
        )
        
        result = response.choices[0].message.content
        return result
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ API Error: {error_msg}")
        
        # Provide helpful troubleshooting
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            st.warning("🔑 Your OpenAI API Key may be invalid. Please check it in the sidebar.")
        elif "rate_limit" in error_msg.lower():
            st.warning("⏱️ Rate limit exceeded. Please wait a moment and try again.")
        elif "model" in error_msg.lower():
            st.info("ℹ️ Your account may not have access to this model. Try using GPT-4 Vision instead.")
        
        return None

# --- 🎨 AI Image Generation Logic ---
def generate_hf_image(prompt, token):
    """
    Connects to the 2026 Hugging Face Router API.
    Handles 503 Service Unavailable by waiting for model to load.
    """
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {token}"}
    
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=60)
            if response.status_code == 200:
                return response.content
            elif response.status_code == 503:
                # Model is warming up; wait based on API suggestion
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

# --- 📸 Image Recognition Section ---
st.markdown("**Option A: Upload Fridge Photo** (Auto-detect ingredients)")
uploaded_image = st.file_uploader("Choose a fridge photo", type=["jpg", "jpeg", "png"], key="fridge_photo")

if uploaded_image is not None:
    if st.button("🔍 Scan Ingredients with AI", use_container_width=True):
        if not openai_api_key:
            st.error("Please enter your OpenAI API Key in the sidebar!")
        else:
            with st.spinner("GPT-4o is analyzing your fridge..."):
                image_bytes = uploaded_image.read()
                detected_ingredients = recognize_fridge_ingredients(image_bytes, openai_api_key)
                
                if detected_ingredients:
                    st.success("✅ Ingredients detected!")
                    st.session_state.detected_ingredients = detected_ingredients
                    st.info(f"**Found:** {detected_ingredients}")

st.markdown("**Option B: Manual Input** (Or combine with detected ingredients)")
if "detected_ingredients" in st.session_state:
    default_ingredients = st.session_state.detected_ingredients
    st.info(f"📋 Pre-filled with detected items. Feel free to edit!")
else:
    default_ingredients = ""

ingredients = st.text_area("What's in your fridge?", placeholder="e.g., 2 eggs, kimchi, chicken breast", height=100, value=default_ingredients)

# --- 🌏 Asian Cuisine Selection (Multi-select) ---
st.markdown("**Cuisine Preference**")
asian_cuisines = {
    "🇨🇳 Chinese": "Chinese",
    "🇯🇵 Japanese": "Japanese", 
    "🇰🇷 Korean": "Korean",
    "🇹🇭 Thai": "Thai",
    "🇮🇳 Indian": "Indian",
    "🇻🇳 Vietnamese": "Vietnamese",
    "🇵🇭 Filipino": "Filipino",
    "🇲🇾 Malaysian": "Malaysian",
    "🇸🇬 Singaporean": "Singaporean",
    "🇮🇩 Indonesian": "Indonesian",
    "🇱🇦 Laotian": "Laotian",
    "🇰🇭 Cambodian": "Cambodian"
}

# Create columns for checkbox layout
cols = st.columns(4)
selected_cuisines = []
for idx, (label, cuisine) in enumerate(asian_cuisines.items()):
    with cols[idx % 4]:
        if st.checkbox(label, value=False, key=f"cuisine_{cuisine}"):
            selected_cuisines.append(cuisine)

if not selected_cuisines:
    st.warning("⚠️ Please select at least one cuisine type!")
    selected_cuisines_text = "any Asian"
else:
    selected_cuisines_text = ", ".join(selected_cuisines)
    st.success(f"✅ Selected: {selected_cuisines_text}")

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
        st.error("Please enter your Groq API Key in the sidebar!")
    else:
        with st.spinner("AI is calculating portions and creative recipes..."):
            try:
                # Inject persistent memory into the system prompt
                recent_mem = ". ".join(load_trimmed_memory())
                
                # Build cuisine constraint
                cuisine_constraint = f"ONLY suggest dishes from these cuisines: {selected_cuisines_text}. Strictly adhere to this cuisine preference." if selected_cuisines else ""
                
                # Instruction to the LLM to maintain a strict parsable structure
                sys_instruct = f"""
                You are FridgeMate, a precise professional chef AI. History: {recent_mem}. 
                {cuisine_constraint}
                Provide exactly 3 distinct meal options based on user inventory.
                
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
                prompt_text = f"Inventory: {ingredients}, Time: {time_avail}, Vibe: {vibe}, Budget: {budget}, Cuisines: {selected_cuisines_text}"

                # Initialize Groq client
                client = Groq(api_key=api_key)
                res = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": sys_instruct}, 
                        {"role": "user", "content": prompt_text}
                    ]
                )
                st.session_state.last_options = res.choices[0].message.content
                st.rerun()
            except Exception as e:
                st.error(f"Logic Error: {e}")

# --- OUTPUT DELIVERY: Parsing & Display ---
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
                m2.write(f"🔥 **Difficulty:** {get_val('LEVEL:')}")
                
                m3, m4 = st.columns(2)
                m3.write(f"🛒 **To Buy:** {get_val('SHOPPING:')}")
                m4.write(f"💰 **Estimated Cost:** {get_val('COST:')}")

                # Detailed Recipe Display
                with st.expander("📖 View Precise Recipe & Instructions"):
                    if "RECIPE:" in opt:
                        recipe_content = opt.split("RECIPE:")[1].split("CAPTION:")[0].strip()
                        st.markdown(recipe_content)

                # --- 🎨 Generate Dual-Image Visuals ---
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
                                
                                st.success("📝 **Recommended Social Media Caption:**")
                                st.write(get_val("CAPTION:"))
                            else:
                                st.error("Image API is currently busy. Please try again.")
                idx += 1

# --- FEEDBACK LOOP: Learning Mechanism ---
st.divider()
st.subheader("📝 Feedback & Learning")
st.write("Help FridgeMate adapt to your taste.")
user_pref = st.text_input("Enter a new preference:", placeholder="e.g., I have a nut allergy...")

if st.button("Submit & Teach AI"):
    if user_pref:
        save_feedback(user_pref)
        st.success("Preference saved! AI memory updated.")
        st.rerun()

st.divider()
st.caption("FridgeMate| 2026 API Compliant")
