import streamlit as st
import os
from langchain_community.agent_toolkits import SQLDatabaseToolkit 
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import AzureChatOpenAI
from langchain.agents.agent_types import AgentType 
from langchain.agents import create_sql_agent
from dotenv import load_dotenv

load_dotenv()

llm = AzureChatOpenAI(deployment_name="gpt-35-turbo", temperature=0, max_tokens=4000)  

db = SQLDatabase.from_uri("sqlite:///Chinook.db")
# Set up SQL toolkit for LangChain Agent  
toolkit = SQLDatabaseToolkit(db=db, llm=llm) 

# Initialize and run the Agent  
agent_executor = create_sql_agent(  
    llm=llm,  
    toolkit=toolkit,  
    verbose=True,  
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  
)

st.title("SQL Query Generator with GPT-35-turbo")
st.write("Enter your question to query chinook db and view results.")

# Input field for the user to type a message
user_message = st.text_input("Enter your message:")

if user_message:
    # Format the system message with the schema
    # Ask Questions  

    # Display the generated SQL query
    try:
        st.write(f"Response: { agent_executor.run(user_message)}")

    except Exception as e:
        st.write(f"An error occurred: {e}")