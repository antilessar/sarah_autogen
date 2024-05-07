Make a .env file with:
DATA_BASE_PATH = "path/to/database/example.db"
OPENAI_API_KEY="examplekey"
OPENAI_API_BASE_ENDPOINT = "https://example.openai.azure.com/"
BASE_DIR=./agent_results


Run:
>python main.py --prompt "prompt your database with a question here"

This code is based off of repository here, specifically v1 branch:
https://github.com/disler/multi-agent-postgres-data-analytics.git
This code allows user to query a sql database