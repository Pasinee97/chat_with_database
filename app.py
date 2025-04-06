import streamlit as st
import pandas as pd
import google.generativeai as genai

st.title("🧠 CSV Chatbot with Query Capability")
st.subheader("Upload a CSV and ask questions about your data")

# Input API key
gemini_api_key = st.text_input("Gemini API Key", type="password", placeholder="Enter your Gemini API Key")

# Initialize Gemini
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("✅ Gemini model initialized.")
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")

# Set up session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.uploaded_data = df
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")

# Chat input
if model and st.session_state.uploaded_data is not None:
    user_input = st.chat_input("Ask a question about your data...")
    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        df = st.session_state.uploaded_data.copy()
        df_name = "df"
        data_dict_text = str(dict(df.dtypes))
        example_record = df.head(2).to_string(index=False)

        # Prompt template
        prompt = f"""
You are a helpful Python code generator.

Your goal is to write Python code snippets based on the user's question and
