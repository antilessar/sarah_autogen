import os
from langchain_community.agent_toolkits import SQLDatabaseToolkit 
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from openai import AzureOpenAI
from langchain_community.chat_models import AzureChatOpenAI
from langchain.agents.agent_types import AgentType 
from langchain.agents import create_sql_agent
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
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
# Ask Questions  
agent_executor.run("how many employees are there?")

