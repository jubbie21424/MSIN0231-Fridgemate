import streamlit as st
from google import genai
from google.genai import types
import requests
import os

# --- Page Configuration ---
# Set up the tab title, icon, and layout width
st.set_page_config(page_title="FridgeMate Pro", page_icon="🍳", layout="centered")

# --- 🧠 SMART MEMORY FUNCTIONS ---
def save_feedback(text):
    """Appends user feedback to a local text file to simulate long-term AI memory."""
    with open("memory.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

def load_trimmed_memory(limit=5):
    """
    Reads the last few memories to stay within the AI's Token/Quota limits.
    Focuses the AI on the most recent user preferences.
    """
    if os.path.exists("memory.txt"):
        with open("memory.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            return lines[-limit:] # Only return the last N entries
    return []

# --- Sidebar: The Learning Loop UI ---
with st.sidebar:
    st.title("⚙️ System Settings")
    # API Key input (Type set to password for security)
    gemini_api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.divider()
    st.header("🧠 Active Session Memory")
    # Display the trimmed memory that the AI is currently "thinking" about
    active_memories = load_trimmed_memory()
    if active_memories:
        st.write("Current AI Preferences:")
        for i, pref in enumerate(active_memories):
            st.caption(f"• {pref}")
        
        # Reset mechanism to clear the memory file
        if st.button("Reset AI Memory"):
            if os.path.exists("memory.txt"): os.remove("memory.txt")
            st.success("Memory cleared!")
            st.rerun()
    else:
        st.write("AI is currently a blank slate.")

# --- Main UI ---
st.title("🍳 FridgeMate")
st.markdown("*Supporting judgement, reducing decision fatigue.*")
st.divider()

# --- INPUT FLOW: Steps to gather user context ---
st.markdown("#### 1. Inventory & Context")
ingredients = st.text_area("What's in your fridge?", placeholder="e.g., 2 eggs, kimchi, tofu", height=100)

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

# --- Action Button: Triggers the AI Decision Process ---
if st.button("Decide for Me", use_container_width=True, type="primary"):
    if not gemini_api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    else:
        try:
            # Initialize the Gemini Client
            client = genai.Client(api_key=gemini_api_key)
            
            # Fetch the trimmed memory to personalize the prompt
            recent_memory_str = ". ".join(load_trimmed_memory())
            
            # System Instruction: Strictly defining the output structure for parsing
            sys_instruct = f"""
            You are FridgeMate. Recent user preferences: {recent_memory_str}
            Provide exactly 2 meal options. 
            
            Structure (MUST use '---' as delimiter):
            ---
            NAME: [Dish Name]
            META: [Prep Time] | [Difficulty]
            COST: [Extra items] | [Estimated Cost in GBP]
            IMG_KEY: [Single food noun for image prompt]
            ING_KEY: [Single raw ingredient noun for image prompt]
            RECIPE: [Specific steps with measurements]
            PLOG_CAPTION: [Emotional Instagram-style caption]
            ---
            """
            
            # Call Gemini 2.0 Flash
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                config=types.GenerateContentConfig(system_instruction=sys_instruct),
                contents=f"Inventory: {ingredients}, Time: {time_avail}, Energy: {energy_level}, Vibe: {vibe}, Budget: {budget}"
            )
            # Store the raw text response in session state
            st.session_state.last_options = response.text
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Quota exceeded? Wait 60s or check your API usage in Google AI Studio.")

# --- OUTPUT DELIVERY: Parsing and displaying AI suggestions ---
if "last_options" in st.session_state and st.session_state.last_options:
    st.markdown("### ✨ Your Matches")
    # Split the AI output into separate dishes using the delimiter
    raw_options = st.session_state.last_options.split("---")
    
    idx = 0
    for opt in raw_options:
        if "NAME:" in opt:
            with st.container(border=True):
                lines = opt.strip().split('\n')
                
                # Helper function to extract specific fields safely
                def get_line(label, default="N/A"):
                    for l in lines:
                        if label in l:
                            return l.replace(label, "").strip()
                    return default

                name = get_line("NAME:", "Dish Name")
                meta = get_line("META:", "N/A")
                cost = get_line("COST:", "No extra cost")
                img_k = get_line("IMG_KEY:", "food")
                ing_k = get_line("ING_KEY:", "ingredients")
                
                st.subheader(name)
                
                # Display Time and Cost metadata
                c_meta, c_cost = st.columns(2)
                c_meta.write(f"⏱️ **Info:** {meta}")
                c_cost.write(f"💰 **Extras:** {cost}")
                
                # Recipe expander
                with st.expander("📖 View Recipe Instructions"):
                    if "RECIPE:" in opt:
                        recipe = opt.split("RECIPE:")[1].split("PLOG_CAPTION:")[0].strip()
                        st.markdown(recipe)

                # --- 🎨 AI IMAGE GENERATION (Via Pollinations.ai) ---
                if st.button(f"✨ Generate Real-Time AI Plog for {name}", key=f"btn_{idx}"):
                    with st.spinner("AI is painting your Plog..."):
                        # Prepare URL-safe prompts for the image generator
                        prompt_done = f"plated {name}, {img_k}, professional food photography, cinematic lighting, 4k".replace(" ", "%20")
                        prompt_raw = f"raw ingredients for {name}, {ing_k}, kitchen counter, aesthetic flatlay, 4k".replace(" ", "%20")

                        # External image generation API URLs
                        url_done = f"https://image.pollinations.ai/prompt/{prompt_done}?nologo=true"
                        url_raw = f"https://image.pollinations.ai/prompt/{prompt_raw}?nologo=true"
        
                        # Display Images side-by-side (Dual-Image Plog)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(url_raw, caption="📸 The Prep")
                        with col2:
                            st.image(url_done, caption="📸 The Result")
                    
                    if "PLOG_CAPTION:" in opt:
                        caption = opt.split("PLOG_CAPTION:")[1].strip()
                        st.info(caption)

                    # Real image download button
                    try:
                        img_data = requests.get(url_done).content
                        st.download_button("📸 Download Plog", data=img_data, file_name=f"{name}.jpg", mime="image/jpeg", key=f"dl_{idx}")
                    except:
                        pass
                
                idx += 1

# --- FEEDBACK LOOP: The Teaching mechanism ---
st.divider()
st.subheader("📝 Feedback & Learning")
st.write("Help FridgeMate adapt to your tastes.")
feedback = st.text_input("Any preferences? (e.g., 'Less salt', 'No onions')")
if st.button("Submit & Teach AI"):
    if feedback:
        save_feedback(feedback)
        st.success("Preference saved! AI memory has been updated.")
        st.rerun()

st.divider()
st.caption("FridgeMate MVP | UCL MSIN0231 | Powered by Gemini 2.0 Flash & Pollinations AI")
