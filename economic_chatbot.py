import streamlit as st
import requests
import google.generativeai as genai
import json
from datetime import datetime
from thefuzz import process, fuzz
import os

# --- Configuration ---
# World Bank API details
WORLD_BANK_API_URL = "https://api.worldbank.org/v2"

# --- Secure Gemini API Key ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "***REMOVED***")  # fallback for local/test only
genai.configure(api_key=GEMINI_API_KEY)

# Indicator mapping for fuzzy matching
INDICATOR_MAPPING = {
    "gdp": "NY.GDP.MKTP.CD",
    "population": "SP.POP.TOTL",
    "inflation": "FP.CPI.TOTL.ZG",
    "co2 emissions": "EN.ATM.CO2E.KT",
    "gdp per capita": "NY.GDP.PCAP.CD",
    "life expectancy": "SP.DYN.LE00.IN",
    "unemployment": "SL.UEM.TOTL.ZS",
}

# --- Caching ---
@st.cache_data(ttl=86400) # Cache for 24 hours
def get_country_list():
    """Fetches and caches the list of countries from the World Bank API."""
    try:
        response = requests.get(f"{WORLD_BANK_API_URL}/country?format=json&per_page=300")
        response.raise_for_status()
        countries = response.json()[1]
        return {country['name'].lower(): country['id'] for country in countries}
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching country list: {e}")
        return {}

# --- Helper Functions ---
def find_best_match(query, choices, scorer=fuzz.WRatio, threshold=80):
    """Finds the best fuzzy match for a query from a list of choices."""
    result = process.extractOne(query, choices, scorer=scorer)
    return result[0] if result and result[1] >= threshold else None

def parse_user_query(query, country_names):
    """Parses the user query to extract indicator, country, and year."""
    query_lower = query.lower()
    
    # Fuzzy match indicator
    indicator_key = find_best_match(query_lower, list(INDICATOR_MAPPING.keys()))
    indicator = INDICATOR_MAPPING.get(indicator_key) if indicator_key else None

    # Fuzzy match country
    country_name = find_best_match(query_lower, country_names)
    country_code = get_country_list().get(country_name) if country_name else None

    # Extract year
    year = None
    for word in query.split():
        if word.isdigit() and len(word) == 4:
            year = int(word)
            break
            
    return indicator, country_code, year, indicator_key, country_name

def get_world_bank_data(indicator, country_code, year):
    """Fetches data from the World Bank API."""
    date_param = f"{year}:{year}" if year else ""
    url = f"{WORLD_BANK_API_URL}/country/{country_code}/indicator/{indicator}?format=json&date={date_param}&mrnev=1"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data[0]['total'] == 0 or not data[1]:
            return None, None
            
        latest_entry = data[1][0]
        value = latest_entry['value']
        actual_year = latest_entry['date']
        
        # Format large numbers
        if value > 1_000_000_000:
            value_str = f"${value/1_000_000_000:,.2f} Billion"
        elif value > 1_000_000:
            value_str = f"${value/1_000_000:,.2f} Million"
        else:
            value_str = f"{value:,.2f}"

        return value_str, actual_year

    except requests.exceptions.RequestException:
        return None, None
    except (IndexError, TypeError):
        return None, None

def get_gpt_response(query):
    """Gets a response from Gemini's generative model, with economic context."""
    try:
        system_prompt = (
            "You are an expert economic assistant. "
            "Always answer with a focus on economics, global trends, and World Bank data. "
            "If you don’t know, say so honestly."
        )
        try:
            model = genai.GenerativeModel("models/gemini-2.0-flash")
            response = model.generate_content([{"role": "user", "parts": [{"text": system_prompt + "\n" + query}]}])
            return response.text.strip()
        except Exception as e:
            models = [m.name for m in genai.list_models()]
            if models:
                fallback = models[0]
                model = genai.GenerativeModel(fallback)
                response = model.generate_content([{"role": "user", "parts": [{"text": system_prompt + "\n" + query}]}])
                return f"(Fallback model: {fallback})\n" + response.text.strip()
            return f"Gemini API error: {e}\nAvailable models: {models}"
    except Exception as e:
        return f"An error occurred with the Gemini API: {e}"


# --- UI Rendering ---
def render_chatbot():
    """Renders the main chatbot interface in Streamlit."""
    
    st.set_page_config(layout="wide", page_title="Economics Chatbot")

    # Custom dark theme styling
    st.markdown("""
        <style>
            .stApp {
                background-color: #0A1224;
                color: #EAEAEA;
            }
            .st-emotion-cache-1c7y2kd {
                background-color: #1E90FF;
            }
            .stChatMessage {
                background-color: #18223F;
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
            }
            .st-emotion-cache-janbn0 {
                background-color: #0A1224;
            }
             h1, h2, h3, h4, h5, h6 {
                color: #EAEAEA;
            }
            .stButton>button {
                border-color: #1E90FF;
                color: #1E90FF;
            }
            .stButton>button:hover {
                background-color: #1E90FF;
                color: #0A1224;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("World Bank & Economics Chatbot")
    
    # Limit session state messages to last 30
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if len(st.session_state.messages) > 30:
        st.session_state.messages = st.session_state.messages[-30:]

    # Display example prompts
    if not st.session_state.messages:
        st.info("Try asking: 'GDP of Pakistan in 2022' or 'What is inflation?'")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle chat input
    if prompt := st.chat_input("Ask about global economics..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = ""  # Initialize the response variable

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                country_names = list(get_country_list().keys())
                indicator, country_code, year, indicator_key, country_name = parse_user_query(prompt, country_names)

                if indicator and country_code:
                    data, data_year = get_world_bank_data(indicator, country_code, year)
                    if data:
                        response = f"The {indicator_key.replace('_', ' ')} of **{country_name.title()}** in **{data_year}** was **{data}**."
                        st.markdown(response)
                    else:
                        response = "Sorry, no World Bank data found for your query. " + get_gpt_response(f"Could not find data for {prompt}. Please provide a helpful explanation.")
                        st.write(response)
                else:
                    response = get_gpt_response(prompt)
                    st.write(response)

        # Always append the response to session state
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Clear chat button
    if st.button("Clear Chat") and st.session_state.messages:
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    # To run this file standalone for testing
    render_chatbot()