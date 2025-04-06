import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai

# --- Layout ---
st.title("🧠 CSV Chatbot with Schema Awareness")
st.subheader("Upload your data and ask questions like a boss!")

# --- API Key ---
gemini_api_key = st.text_input("🔑 Gemini API Key", type="password", placeholder="Paste your Gemini API Key here")

model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("✅ Gemini model initialized.")
    except Exception as e:
        st.error(f"❌ Failed to initialize Gemini: {e}")

# --- Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "transaction_data" not in st.session_state:
    st.session_state.transaction_data = None
if "data_dictionary" not in st.session_state:
    st.session_state.data_dictionary = None

# --- Upload Files ---
st.subheader("📁 Upload Your Files")

col1, col2 = st.columns(2)
with col1:
    transaction_file = st.file_uploader("Transaction CSV", type=["csv"], key="transactions")
with col2:
    dict_file = st.file_uploader("Data Dictionary CSV", type=["csv"], key="data_dict")

# --- Load Files ---
if transaction_file:
    try:
        df = pd.read_csv(transaction_file)
        st.session_state.transaction_data = df
        st.write("✅ Transaction Data Preview")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Could not load transaction file: {e}")

if dict_file:
    try:
        data_dict_df = pd.read_csv(dict_file)
        st.session_state.data_dictionary = data_dict_df
        st.write("✅ Data Dictionary Preview")
        st.dataframe(data_dict_df)
    except Exception as e:
        st.error(f"❌ Could not load data dictionary file: {e}")

# --- Chatbot Section ---
if model and st.session_state.transaction_data is not None and st.session_state.data_dictionary is not None:
    user_input = st.chat_input("Ask a question about your data...")

    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        df = st.session_state.transaction_data.copy()
        df_name = "df"
        data_dict_text = st.session_state.data_dictionary.to_string(index=False)
        example_record = df.head(2).to_string(index=False)

        # --- Gemini Prompt with Schema Awareness ---
        prompt = f"""
You are a helpful Python code generator.

Your goal is to write Python code snippets based on the user's question and the provided DataFrame.

**User Question:**
{user_input}

**DataFrame Name:**
{df_name}

**Data Dictionary (Column Descriptions):**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that answers the user's question using the DataFrame.
2. Use pd.to_datetime() for dates if needed.
3. Do NOT include any import statements.
4. Use exec() to execute the code.
5. Store the result in a variable called ANSWER.
6. Assume the DataFrame is already loaded as `{df_name}`.
"""

        try:
            # Generate code from Gemini
            response = model.generate_content(prompt)
            generated_code = response.text

            # Clean up markdown/code fences
            clean_code = generated_code.strip()
            if clean_code.startswith("```"):
                clean_code = clean_code.strip("` \npython").strip("` \n")

            # Remove import lines
            clean_code = "\n".join(
                line for line in clean_code.splitlines()
                if not line.strip().lower().startswith("import")
                and not line.strip().lower().startswith("from ")
            ).strip()

            # Show code
            with st.expander("📜 Show generated code"):
                st.code(clean_code, language="python")

            # Local vars for safe execution
            local_vars = {
                "df": df,
                "pd": pd,
                "datetime": datetime,
            }

            # Execute code
            exec(clean_code, {}, local_vars)
            ANSWER = local_vars.get("ANSWER", "No result returned.")

            # Display answer
            if isinstance(ANSWER, (pd.DataFrame, pd.Series, dict, list)):
                st.chat_message("assistant").write(ANSWER)
            else:
                st.chat_message("assistant").markdown(f"**Answer:**\n\n{ANSWER}")

            st.session_state.chat_history.append(("assistant", str(ANSWER)))

        except Exception as e:
            st.error(f"❌ Error while generating or executing code: {e}")
else:
    st.info("📌 Please upload both the transaction CSV and data dictionary to begin.")
