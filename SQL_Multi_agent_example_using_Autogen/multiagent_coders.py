import os
from dotenv import load_dotenv
import openai
import autogen
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from prompts import query_maker_gpt_system_prompt, admin_prompt, data_engineer_prompt,\
    code_writer_system_message
from langchain.prompts import PromptTemplate
# import mysql.connector
from openai import AzureOpenAI
import sqlite3
from database_utils import get_csv_files, create_sqlite_database, get_schema, generate_sql_prompt
from dataclasses import dataclass
import tempfile

from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor
#load env variables
load_dotenv()

# openai api key
api_key=os.getenv('OPENAI_API_KEY')
# Set your LLms Endpoint
config_list_gpt_turbo = autogen.config_list_from_models(model_list=[ "gpt-3.5-turbo"])


def query_maker(user_input):
    openaiLLM = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7,
                                        openai_api_key=api_key, cache=False)

    prompt_template = PromptTemplate.from_template(
        "{system_prompt} + '\n' +  {user_input}.")
    csv_files = get_csv_files(os.getenv("CSV_DATA"))
    db_conn = create_sqlite_database(csv_files)
    schemas = get_schema(csv_files)

    query_maker_gpt_system_prompt_general = generate_sql_prompt(schemas)

    chain = LLMChain(llm=openaiLLM, prompt=prompt_template)

    query=chain.run({"system_prompt": query_maker_gpt_system_prompt_general, "user_input": user_input})
    return query

def run_sql_query(sql_query, db="database.db"):
    conn = sqlite3.connect(f'{db}')  # Connect to your SQLite database
    cursor = conn.cursor()
    # conn = mysql.connector.connect(**config)

    cursor = conn.cursor()
    try:
        # Execute SQL queries
        cursor.execute(sql_query)
        result = cursor.fetchall()
    except Exception as e:
        return e

    return result

gpt_turbo_simple_config = {
    # "use_cache": False,
    "temperature": 0.5,
    "config_list": config_list_gpt_turbo,
    # "request_timeout": 90
    }


gpt_turbo_config = {
    # "use_cache": False,
    "temperature": 0.7,
    "config_list": config_list_gpt_turbo,
    # "request_timeout": 90,
    "functions" : [
    {
        "name": "query_maker",
        "description": "generates sql query as per user input",
        "parameters": {
            "type": "object",
            "properties": {
                "user_input": {
                    "type": "string",
                    "description": "This is the input from the user side.",
                }
                ,
            },
            "required": ["user_input"],
        },
    },

{
        "name": "run_sql_query",
        "description": "This function is used to run sql query against user input to get the results.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "This is the mysql query.",
                }
                ,
            },
            "required": ["sql_query"],
        },
    }



    ]
}
function_map={"query_maker": query_maker ,"run_sql_query": run_sql_query}
termination_msg="If everything looks good, respond with Approved."

def is_termination_msg(content):
    have_content=content.get("content", None) is not None
    if have_content and "Approved" in content["content"]:
        return True
    else:
        return False


user_proxy = autogen.UserProxyAgent(
   name="Admin",
   system_message= admin_prompt + termination_msg,
   human_input_mode="NEVER",
    is_termination_msg=is_termination_msg,
    code_execution_config={"work_dir": "coding", "use_docker": False}


)

engineer = autogen.AssistantAgent(
    name="Data_Engineer",
    llm_config=gpt_turbo_config,
    system_message=data_engineer_prompt + termination_msg,
    function_map=function_map
)

# for data visualization
coder = ConversableAgent(
    name="Coder",  # the default assistant agent is capable of solving problems with code
    llm_config=gpt_turbo_config,
    system_message = code_writer_system_message + termination_msg,
    code_execution_config = False
)

critic = autogen.AssistantAgent(
    name="Critic",
    system_message="""Critic. You are a helpful assistant highly skilled in evaluating the quality of a given visualization code by providing a score from 1 (bad) - 10 (good) while providing clear rationale. YOU MUST CONSIDER VISUALIZATION BEST PRACTICES for each evaluation. Specifically, you can carefully evaluate the code across the following dimensions
- bugs (bugs):  are there bugs, logic errors, syntax error or typos? Are there any reasons why the code may fail to compile? How should it be fixed? If ANY bug exists, the bug score MUST be less than 5.
- Data transformation (transformation): Is the data transformed appropriately for the visualization type? E.g., is the dataset appropriated filtered, aggregated, or grouped  if needed? If a date field is used, is the date field first converted to a date object etc?
- Goal compliance (compliance): how well the code meets the specified visualization goals?
- Visualization type (type): CONSIDERING BEST PRACTICES, is the visualization type appropriate for the data and intent? Is there a visualization type that would be more effective in conveying insights? If a different visualization type is more appropriate, the score MUST BE LESS THAN 5.
- Data encoding (encoding): Is the data encoded appropriately for the visualization type?
- aesthetics (aesthetics): Are the aesthetics of the visualization appropriate for the visualization type and the data?

YOU MUST PROVIDE A SCORE for each of the above dimensions.
{bugs: 0, transformation: 0, compliance: 0, type: 0, encoding: 0, aesthetics: 0}
Do not suggest code.
Finally, based on the critique above, suggest a concrete list of actions that the coder should take to improve the code.
""",
    llm_config=gpt_turbo_config,
)

# register the functions
user_proxy.register_function(function_map={"query_maker": query_maker ,"run_sql_query": run_sql_query},)

# Create a temporary directory to store the code files.
temp_dir = tempfile.TemporaryDirectory()

# Create a local command line code executor.
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # Timeout for each code execution in seconds.
    work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
)

# Create an agent with code executor configuration.
code_executor_agent = ConversableAgent(
    "code_executor_agent",
    llm_config=False,  # Turn off LLM for this agent.
    code_execution_config={"work_dir": "coding", "use_docker": False},  # Use the local command line code executor.
    human_input_mode="ALWAYS",  # Always take human input for this agent for safety.
)  

@dataclass
class ExecutorGroupchat(autogen.GroupChat):
    dedicated_executor: autogen.UserProxyAgent = None

    def select_speaker(
        self, last_speaker: autogen.ConversableAgent, selector: autogen.ConversableAgent
    ):
        """Select the next speaker."""

        try:
            message = self.messages[-1]
            if "function_call" in message:
                return self.dedicated_executor
        except Exception as e:
            print(e)
            pass

        selector.update_system_message(self.select_speaker_msg())
        final, name = selector.generate_oai_reply(
            self.messages
            + [
                {
                    "role": "system",
                    "content": f"Read the above conversation. Then select the next role from {self.agent_names} to play. Only return the role.",
                }
            ]
        )
        if not final:
            # i = self._random.randint(0, len(self._agent_names) - 1)  # randomly pick an id
            return self.next_agent(last_speaker)
        try:
            return self.agent_by_name(name)
        except ValueError:
            return self.next_agent(last_speaker)
        

gpt_turbo_config_manager = gpt_turbo_config.copy()
gpt_turbo_config_manager.pop("functions", None)
gpt_turbo_config_manager.pop("tools", None)
groupchat = ExecutorGroupchat(agents=[user_proxy, engineer, coder,code_executor_agent,critic], messages=[], max_round=20,\
                              dedicated_executor=user_proxy)
manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=gpt_turbo_config_manager,
    is_termination_msg= lambda x: "GROUPCHAT_TERMINATE" in x.get("content", ""),
)

user_proxy.initiate_chat( manager,
    message="""Which customer category is company Jackson, Newman and Garcia??""", clear_history=True
)
