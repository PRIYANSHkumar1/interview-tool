import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

# Setting up the Streamlit page configuration
st.set_page_config(page_title="StreamlitChatMessageHistory", page_icon="💬")
st.title("Chatbot")

# Initialize session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []


# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# Setup stage for collecting user details
if not st.session_state.setup_complete:
    st.subheader('Personal Information')

    # Initialize session state for personal information
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

   
    # Get personal information input
    st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], placeholder="Enter your name", max_chars=40)
    st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", max_chars=200)
    st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", max_chars=200)

    
    # Company and Position Section
    st.subheader('Company and Position')

    # Initialize session state for company and position information and setting default values 
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose level",
            key="visibility",
            options=["Junior", "Mid-level", "Senior"],
            index=["Junior", "Mid-level", "Senior"].index(st.session_state["level"])
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"),
            index=("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst").index(st.session_state["position"])
        )

    st.session_state["company"] = st.selectbox(
        "Select a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
        index=("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(st.session_state["company"])
    )

    # Button to complete setup
    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")

# Interview phase
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
    """
    Start by introducing yourself
    """,
    icon="👋",
    )

    # Configure OpenAI client with proper headers for OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"],
        default_headers={
            "HTTP-Referer": "https://streamlit.app",  # Replace with your actual site URL
            "X-Title": "Streamlit Interview Chatbot"
        }
    )
    

    # Setting LLM model if not already initialized
    if "llm_model" not in st.session_state:
        st.session_state["llm_model"] = "meta-llama/llama-4-maverick:free"

    # Initializing the system prompt for the chatbot
    if not st.session_state.messages:
        system_prompt = (f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                        f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                        f"You should interview them for the position {st.session_state['level']} {st.session_state['position']} "
                        f"at the company {st.session_state['company']}")
        st.session_state.messages = [{"role": "system", "content": system_prompt}]

    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Handle user input and Anthropic response
    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your response", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    # Create a message placeholder
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    # Convert messages to OpenAI format
                    openai_messages = []
                    for message in st.session_state.messages:
                        if message["role"] == "system":
                            openai_messages.append({"role": "system", "content": message["content"]})
                        elif message["role"] == "user":
                            openai_messages.append({"role": "user", "content": message["content"]})
                        elif message["role"] == "assistant":
                            openai_messages.append({"role": "assistant", "content": message["content"]})
                    
                    # Stream the response
                    stream = client.chat.completions.create(
                        model=st.session_state["llm_model"],
                        messages=openai_messages,
                        stream=True,
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            text_chunk = chunk.choices[0].delta.content
                            full_response += text_chunk
                            message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    
                    # Add the response to messages
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Increment the user message count
            st.session_state.user_message_count += 1

    # Check if the user message count reaches 5
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

# Show "Get Feedback" 
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Configure OpenAI client for feedback with proper headers
    feedback_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"],
        default_headers={
            "HTTP-Referer": "https://streamlit.app",  # Replace with your actual site URL
            "X-Title": "Streamlit Interview Chatbot"
        }
    )
   

    # System prompt for feedback
    feedback_system_prompt = """You are a helpful tool that provides feedback on an interviewee's performance.
    Before the Feedback give a score of 1 to 10.
    Follow this format:
    Overall Score: //Your score
    Feedback: //Here you put your feedback
    Give only the feedback do not ask any additional questions."""

    # Generate feedback using Llama 4 Maverick
    feedback_response = feedback_client.chat.completions.create(
        model="meta-llama/llama-4-maverick:free",
        messages=[
            {"role": "system", "content": feedback_system_prompt},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any conversation: {conversation_history}"}
        ],
    )

    st.write(feedback_response.choices[0].message.content)

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
