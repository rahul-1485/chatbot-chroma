# app.py
import streamlit as st
from supabase import create_client, Client
import os

st.title("💬 GenAI Chat with Supabase")

# Supabase connection
# Read from secrets.toml
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# Chat UI
user = st.text_input("Your name:")
msg = st.text_input("Your message:")

if st.button("Send"):
    # Simple AI response (mock or API call)
    response = f"AI Response to: {msg}"

    # Store in DB
    supabase.table("chat_history").insert({
        "user_name": user,
        "message": msg,
        "response": response
    }).execute()

    st.success("Message saved!")
    st.write(response)

# Display history
if st.button("Show History"):
    data = supabase.table("chat_history").select("*").execute()
    for row in data.data:
        st.write(f"**{row['user_name']}**: {row['message']} → {row['response']}")
