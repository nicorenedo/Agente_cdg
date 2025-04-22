import streamlit as st
import sys
from pathlib import Path

# Set the page title
st.set_page_config(page_title="Agent Interaction")

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "backend" / "src"))

from agentic_patterns_azure.planning_pattern.react_agent import ReactAgent
from defined_tools import sum_two_elements, multiply_two_elements, compute_log

# Initialize the agent with the imported tools
agent = ReactAgent(tools=[sum_two_elements, multiply_two_elements, compute_log])

# Streamlit UI
st.title("Agent Interaction")
st.write("Enter your query below to interact with the agent.")

# Input box for user query
user_query = st.text_input("User Query:", "")

# File uploader for user file
uploaded_file = st.file_uploader("Upload a file for processing (optional):", type=["txt", "csv", "json"])

if st.button("Submit"):
    if user_query.strip() or uploaded_file:
        with st.spinner("Processing..."):
            try:
                if uploaded_file:
                    # Read the uploaded file content
                    file_content = uploaded_file.read().decode("utf-8")
                    st.write("File content:")
                    st.code(file_content)
                    # Process the file content with the agent
                    response = agent.run(user_msg=user_query, file_content=file_content)
                else:
                    # Process only the user query
                    response = agent.run(user_msg=user_query)
                
                st.success("Response:")
                st.write(response)
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a query or upload a file.")
