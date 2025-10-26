# app.py
import streamlit as st
from supabase import create_client, Client
from groq import Groq
import os
from datetime import datetime

st.set_page_config(page_title="GenAI Chat", page_icon="💬", layout="wide")

st.title("💬 GenAI Chat with Supabase & Groq")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Initialize Groq
@st.cache_resource
def init_groq():
    api_key = st.secrets["groq"]["api_key"]
    return Groq(api_key=api_key)

supabase = init_supabase()
groq_client = init_groq()

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar for user login
with st.sidebar:
    st.header("User Settings")
    if st.session_state.user is None:
        user_input = st.text_input("Enter your name:")
        if st.button("Login", use_container_width=True):
            if user_input.strip():
                st.session_state.user = user_input.strip()
                st.rerun()
            else:
                st.error("Please enter a valid name")
    else:
        st.success(f"Logged in as: **{st.session_state.user}**")
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()
    
    st.divider()
    
    # History controls
    st.header("Chat History")
    if st.button("📜 Load History", use_container_width=True):
        try:
            data = supabase.table("chat_history").select("*").order("created_at", desc=False).limit(50).execute()
            st.session_state.messages = []
            for row in data.data:
                st.session_state.messages.append({
                    "role": "user",
                    "content": row['message'],
                    "user_name": row['user_name']
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": row['response']
                })
            st.success(f"Loaded {len(data.data)} messages")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading history: {str(e)}")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
if st.session_state.user is None:
    st.info("👈 Please login with your name in the sidebar to start chatting")
else:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user" and "user_name" in message:
                st.markdown(f"**{message['user_name']}**: {message['content']}")
            else:
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "user_name": st.session_state.user
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(f"**{st.session_state.user}**: {prompt}")
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Call Groq API
                    chat_completion = groq_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant. Be concise and friendly."},
                            *[{"role": m["role"], "content": m["content"]} 
                              for m in st.session_state.messages[-10:]]  # Last 10 messages for context
                        ],
                        model="llama-3.3-70b-versatile",  # or "mixtral-8x7b-32768"
                        temperature=0.7,
                        max_tokens=1024,
                    )
                    
                    response = chat_completion.choices[0].message.content
                    st.markdown(response)
                    
                    # Add assistant response to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    # Save to database
                    try:
                        supabase.table("chat_history").insert({
                            "user_name": st.session_state.user,
                            "message": prompt,
                            "response": response,
                            "created_at": datetime.utcnow().isoformat()
                        }).execute()
                    except Exception as db_error:
                        st.warning(f"Message sent but not saved to DB: {str(db_error)}")
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

# Footer
st.divider()
st.caption("Powered by Groq LLM & Supabase 🚀")