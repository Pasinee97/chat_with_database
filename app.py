
import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai

st.title("🧠 CSV Chatbot with Schema Support")

# --- Load Gemini API Key from secrets ---
try:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])
    st.success("✅ Gemini model initialized.")
except Exception as e:
    st.error(f"❌ Failed to initialize Gemini: {e}")
    model = None

# --- File Uploads ---
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("📁 Upload CSV File (Transaction Data)", type=["csv"])
with col2:
    dict_file = st.file_uploader("📄 Upload Data Dictionary (Optional)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
        st.write("✅ Transaction Data Preview")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Error loading transaction CSV: {e}")

if dict_file:
    try:
        data_dict_df = pd.read_csv(dict_file)
        st.session_state.data_dict_df = data_dict_df
        st.write("📘 Data Dictionary Preview")
        st.dataframe(data_dict_df)
    except Exception as e:
        st.error(f"❌ Error loading data dictionary: {e}")

# --- Display chat history ---
if model and "chat" in st.session_state:
    for message in st.session_state.chat.history:
        with st.chat_message("assistant" if message.role == "model" else "user"):
            st.markdown(message.parts[0].text)

# --- Chat input handling ---
if model and "chat" in st.session_state and "df" in st.session_state:
    if user_input := st.chat_input("Ask a question about your data..."):
        st.chat_message("user").markdown(user_input)

        df = st.session_state.df.copy()
        df_name = "df"
        schema = str(dict(df.dtypes))
        sample_rows = df.head(2).to_string(index=False)
        dictionary_text = st.session_state.data_dict_df.to_string(index=False) if "data_dict_df" in st.session_state else "N/A"

        # --- Prompt to generate code ---
        code_prompt = f"""
You are a helpful Python code generator.

**User Question:**
{user_input}

**DataFrame Name:** {df_name}

**DataFrame Schema:**
{schema}

**Sample Rows:**
{sample_rows}

**Data Dictionary (Column Descriptions):**
{dictionary_text}

**Instructions:**
- Write Python code that answers the question using the DataFrame.
- Use pd.to_datetime() if needed.
- Do NOT use import statements.
- Save the final result in a variable called ANSWER.
- Assume the DataFrame is already loaded as {df_name}.
- Only return code (no explanation or markdown formatting).
"""

        try:
            code_response = st.session_state.chat.send_message(code_prompt)
            raw_code = code_response.text.strip()

            # Clean up markdown fences
            if raw_code.startswith("```"):
                raw_code = raw_code.strip("` \npython").strip("` \n")

            # Remove import lines
            cleaned_code = "\n".join(
                line for line in raw_code.splitlines()
                if not line.strip().lower().startswith("import")
                and not line.strip().lower().startswith("from ")
            )

            with st.expander("🧠 Generated Python Code"):
                st.code(cleaned_code, language="python")

            # Execute code
            local_vars = {"df": df, "pd": pd, "datetime": datetime}
            exec(cleaned_code, {}, local_vars)
            answer = local_vars.get("ANSWER", "No result returned.")

            # --- Prompt for explanation ---
            explain_prompt = f"""
You are a helpful assistant.

The user asked: "{user_input}"

The Python result is: {answer}

Please explain the result in clear and friendly language.
"""

            explanation_response = model.generate_content(explain_prompt)
            explanation = explanation_response.text.strip()

            st.chat_message("assistant").markdown(explanation)

        except Exception as e:
            st.error(f"❌ Error processing request: {e}")
else:
    st.info("📌 Please upload your transaction CSV to start.")
