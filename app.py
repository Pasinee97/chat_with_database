import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai

# App layout
st.title("🧠 CSV Chatbot with Query Capability")
st.subheader("Upload your CSV and ask questions!")

# API Key
gemini_api_key = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste your Gemini API Key here")

# Init Gemini
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("✅ Gemini model initialized.")
    except Exception as e:
        st.error(f"❌ Failed to initialize Gemini: {e}")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None

# File upload
uploaded_file = st.file_uploader("📄 Upload a CSV file", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.uploaded_data = df
        st.write("### Preview of your data:")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")

# Chat
if model and st.session_state.uploaded_data is not None:
    user_input = st.chat_input("Ask a question about your data...")
    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        df = st.session_state.uploaded_data.copy()
        df_name = "df"
        data_dict_text = str(dict(df.dtypes))
        example_record = df.head(2).to_string(index=False)

        # Gemini prompt
        prompt = f"""
You are a helpful Python code generator.

Your job is to generate Python code that answers the user's question using the DataFrame provided.

**User Question:**
{user_input}

**DataFrame Name:** {df_name}

**DataFrame Structure:**
{data_dict_text}

**Example Data (top 2 rows):**
{example_record}

**Instructions:**
1. Use Python code to answer the question.
2. Use `exec()` to execute the code.
3. Do NOT use `import` or `from ... import`.
4. Convert date columns with `pd.to_datetime()` if needed.
5. Store the final answer in a variable named `ANSWER`.
6. The DataFrame is already loaded as `{df_name}`.
"""

        try:
            # Generate code from Gemini
            response = model.generate_content(prompt)
            generated_code = response.text

            # Clean up code
            clean_code = generated_code.strip()
            if clean_code.startswith("```"):
                clean_code = clean_code.strip("` \npython").strip("` \n")

            # Remove all import statements
            clean_code = "\n".join(
                line for line in clean_code.splitlines()
                if not line.strip().lower().startswith("import")
                and not line.strip().lower().startswith("from ")
            ).strip()

            # Show code for transparency
            with st.expander("📜 Show generated code"):
                st.code(clean_code, language="python")

            # Safe local execution environment
            local_vars = {
                "df": df,
                "pd": pd,
                "datetime": datetime,
            }

            exec(clean_code, {}, local_vars)

            # Get the answer
            ANSWER = local_vars.get("ANSWER", "No result returned.")

            # Display the result
            if isinstance(ANSWER, (pd.DataFrame, pd.Series, dict, list)):
                st.chat_message("assistant").write(ANSWER)
            else:
                st.chat_message("assistant").markdown(f"**Answer:**\n\n{ANSWER}")

            st.session_state.chat_history.append(("assistant", str(ANSWER)))

        except Exception as e:
            st.error(f"❌ Error during execution: {e}")
else:
    st.info("📌 Upload a CSV file and provide your Gemini API key to begin.")
