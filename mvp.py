import streamlit as st
from google import genai
from google.genai import types

# --- Page Configuration ---
st.set_page_config(page_title="FridgeMate MVP", page_icon="🍳", layout="centered")

# --- Initialize Session Memory (The Learning Loop) ---
# We use session_state to simulate a persistent user profile during the demo
if "preference_memory" not in st.session_state:
    st.session_state.preference_memory = [] 
if "last_options" not in st.session_state:
    st.session_state.last_options = None

# --- Sidebar: System Settings & Memory Display ---
with st.sidebar:
    st.title("⚙️ System Settings")
    gemini_api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.divider()
    st.header("🧠 AI Learned Memory")
    # Displaying what the AI has "learned" from user feedback
    if st.session_state.preference_memory:
        for i, pref in enumerate(st.session_state.preference_memory):
            st.caption(f"{i+1}. {pref}")
        if st.button("Reset AI Memory"):
            st.session_state.preference_memory = []
            st.rerun()
    else:
        st.write("AI is currently a blank slate. Provide feedback after cooking!")

# --- Main UI ---
st.title("🍳 FridgeMate")
st.markdown("*Supporting judgement, reducing decision fatigue.*")
st.divider()

# --- USER INPUT FLOW (Steps 1-4) ---
# 1. Inventory Input (Natural Language)
st.markdown("#### 1. Inventory Input")
ingredients = st.text_area("What's in your fridge?", 
                           placeholder="e.g., 2 eggs, 1 block of tofu, leftover kimchi, half a chicken breast", 
                           height=100)

# 2. Contextual Constraints (Time, Energy, Mood)
st.markdown("#### 2. Contextual Constraints")
c1, c2, c3 = st.columns(3)
with c1:
    time_avail = st.select_slider("Time Available", options=["15min", "30min", "1hr+"])
with c2:
    energy_level = st.select_slider("Energy Level", options=["Low", "Medium", "High"])
with c3:
    vibe = st.text_input("Mood / Vibe", placeholder="e.g., Spicy comfort food")

# 3. Budget & 4. Grocery Access
st.markdown("#### 3. Budget & 4. Grocery Access")
col_a, col_b = st.columns(2)
with col_a:
    budget = st.text_input("Additional Budget", placeholder="e.g., £5 or less")
with col_b:
    grocery_access = st.selectbox("Asian Grocery Access", ["Limited Access", "Occasional", "Frequent"])

# --- Action Button ---
if st.button("Decide for Me", use_container_width=True, type="primary"):
    if not gemini_api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not ingredients:
        st.warning("Inventory cannot be empty.")
    else:
        try:
            client = genai.Client(api_key=gemini_api_key)
            
            # Combine past feedbacks to guide the AI
            memory_str = ". ".join(st.session_state.preference_memory)
            
            # System Instruction: Strictly defining the persona and output structure
            sys_instruct = f"""
            You are FridgeMate, an expert culinary decision assistant for Asian diaspora in the UK.
            User's Historical Preferences: {memory_str}

            Task: Provide exactly 2-3 meal options based on input.
            
            Recipe Requirements: 
            - Be extremely specific with measurements (e.g., '1 tbsp soy sauce', '2 tsp sugar').
            - Steps must be short, action-oriented, and concise.

            Output Structure (MUST use '---' as delimiter):
            ---
            NAME: [Dish Name] - [Short Plog-style Description]
            META: [Prep Time] | [Difficulty Level]
            COST: [Additional items to buy & estimated cost in GBP]
            RECIPE: [3-5 concrete steps with exact seasoning amounts]
            ---
            """
            
            user_msg = f"""
            Ingredients: {ingredients}
            Context: {time_avail} minutes, {energy_level} energy, {vibe} vibe.
            Budget: {budget}.
            Grocery Access: {grocery_access}.
            """

            # Calling Gemini 2.5 Flash for high-speed reasoning
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(system_instruction=sys_instruct),
                contents=user_msg
            )
            
            st.session_state.last_options = response.text
            
        except Exception as e:
            st.error(f"AI Connection Error: {e}")

# --- OUTPUT DELIVERY ---
if st.session_state.last_options:
    st.markdown("### ✨ Your Best Matches")
    # Split the raw AI text into individual cards using the delimiter
    raw_options = st.session_state.last_options.split("---")
    
    # We use enumerate(i) to generate unique keys for buttons and avoid DuplicateElementKey errors
    for i, opt in enumerate(raw_options):
        if "NAME:" in opt:
            with st.container(border=True):
                lines = opt.strip().split('\n')
                
                # Extracting specific fields from AI response
                dish_name = next((l for l in lines if "NAME:" in l), "NAME: Unknown").replace("NAME:", "").strip()
                meta_info = next((l for l in lines if "META:" in l), "META: N/A").replace("META:", "").strip()
                cost_info = next((l for l in lines if "COST:" in l), "COST: £0").replace("COST:", "").strip()
                
                st.subheader(dish_name)
                
                col_m, col_c = st.columns(2)
                col_m.write(f"⏱️ **Info:** {meta_info}")
                col_c.write(f"💰 **Extra:** {cost_info}")
                
                # Expandable Recipe Section
                with st.expander("📖 View Step-by-Step Recipe"):
                    if "RECIPE:" in opt:
                        # Extract everything after the RECIPE: label
                        recipe_content = opt.split("RECIPE:")[1].strip()
                        st.markdown(recipe_content)
                    else:
                        st.write("Recipe details unavailable.")
                
                # Output Delivery Points 4 & 5 (Interactive Buttons)
                b1, b2 = st.columns(2)
                # Using unique keys f"img_{i}" to prevent Streamlit Errors
                b1.button("🖼️ Preview Image/Video", key=f"img_{i}", use_container_width=True)
                b2.button("🔗 Full Plog Content", key=f"plog_{i}", use_container_width=True)

    # --- FEEDBACK LOOP (Memory Mechanism) ---
    st.divider()
    st.subheader("📝 Feedback for Personalization")
    feedback = st.text_input("How was this suggestion? (AI will learn from this)", 
                             placeholder="e.g., 'A bit too salty', 'I prefer more garlic', 'No more tofu please'")
    
    if st.button("Submit Feedback & Teach AI"):
        if feedback:
            # Store feedback in session memory
            st.session_state.preference_memory.append(feedback)
            st.success("Preference saved! Next time, I'll adjust the seasonings and choices for you.")
            # Reset view to show updated memory on next run
            st.session_state.last_options = None
            st.rerun()

# --- Footer ---
st.divider()
st.caption("UCL MSIN0231 | FridgeMate MVP Framework | Powered by Gemini 2.5 Flash")