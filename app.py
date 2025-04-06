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

Your goal is to write Python code snippets based on the user's question and the provided DataFrame.

**User Question:**
{user_input}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that answers the user's question by querying or manipulating the DataFrame.
2. Use the exec() function to execute the code.
3. Do NOT import pandas.
4. Convert date columns using pd.to_datetime().
5. Store the result in a variable named ANSWER.
6. Assume the DataFrame is already loaded as {df_name}.
"""

        try:
            # Get code from Gemini
            response = model.generate_content(prompt)
            generated_code = response.text

            # Strip markdown formatting if present
            clean_code = generated_code.strip()
            if clean_code.startswith("```"):
                clean_code = clean_code.strip("` \npython").strip("` \n")

            # Show generated code
            with st.expander("Show generated code"):
                st.code(clean_code, language="python")

            # Execute the generated code
            local_vars = {"df": df, "pd": pd}
            exec(clean_code, {}, local_vars)

            # Display result from ANSWER
            ANSWER = local_vars.get("ANSWER", "No result returned.")
            st.chat_message("assistant").markdown(f"**Answer:**\n\n{ANSWER}")
            st.session_state.chat_history.append(("assistant", str(ANSWER)))
        except Exception as e:
            st.error(f"❌ Error while generating or executing code: {e}")
else:
    st.info("📌 Please upload a CSV file and enter your Gemini API key.")
