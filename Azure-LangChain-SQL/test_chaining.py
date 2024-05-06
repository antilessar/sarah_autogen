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
# Define the answer prompt template
answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

Question: {question}
SQL Query: {query}
SQL Result: {result}
Answer: """
)

os.environ["OPENAI_API_TYPE"] = "azure"  
os.environ["OPENAI_API_KEY"] = "b10b7b55f3fb49e5917ce25931122bf5"
os.environ["OPENAI_API_BASE"] = "https://sql-qna-azureopenai.openai.azure.com/"  
os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview" 
llm = AzureChatOpenAI(deployment_name="gpt-35-turbo", temperature=0, max_tokens=4000)  

db = SQLDatabase.from_uri("sqlite:///Chinook.db")
# Set up SQL toolkit for LangChain Agent  
toolkit = SQLDatabaseToolkit(db=db, llm=llm) 


execute_query = QuerySQLDataBaseTool(db=db)
write_query = create_sql_query_chain(llm, db)

# Chain setup
answer = answer_prompt | llm | StrOutputParser() 

chain = (
    RunnablePassthrough.assign(query=write_query).assign(
        result=itemgetter("query") | execute_query
    )
    | answer
)

# # Invoke the chain with the question
response = chain.invoke({"question": "How many employees are there"})
print(response)
