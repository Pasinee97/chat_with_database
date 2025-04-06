import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

st.title("🧠 CSV Chatbot with Query Capability")
st.subheader("Upload CSV and Ask Data Questions")

# Input API key
gemini_api_key = st.text_input("Gemini API Key", type="password", placeholder="Enter your Gemini API Key")

# Initialize Gemini model
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("Gemini is ready!")
    except Exception as e:
        st.error(f"Gemini setup failed: {e}")

# Session state
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
        st.error(f"Error reading file: {e}")

# Chat UI
if model and st.session_state.uploaded_data is not None:
    question = st.chat_input("Ask a question about your data...")
    if question:
        st.chat_message("user").markdown(question)
        st.session_state.chat_history.append(("user", question))

        df = st.session_state.uploaded_data.copy()
        df_name = "df"
        data_dict_text = str(dict(df.dtypes))
        example_record = df.head(2).to_string(index=False)

        prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question and the provided DataFrame information.

**User Question:**
{question}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
2. Use the `exec()` function to execute the generated code.
3. Do not import pandas.
4. Convert any date columns using pd.to_datetime().
5. Store the result in a variable called `ANSWER`.
6. Assume the DataFrame is already loaded as `{df_name}`.
"""

        try:
            # Get code from Gemini
            response = model.generate_content(prompt)
            generated_code = response.text

            # Show generated code (optional for debugging)
            with st.expander("Show generated code"):
                st.code(generated_code, language="python")

            # Execute generated code
            local_vars = {"df": df, "pd": pd}
            exec(generated_code, {}, local_vars)

            # Show the answer
            ANSWER = local_vars.get("ANSWER", "No result returned.")
            st.chat_message("assistant").markdown(f"**Answer:**\n\n{ANSWER}")
            st.session_state.chat_history.append(("assistant", str(ANSWER)))
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV and enter your API key to get started.")
