# sarah_autogen

To make sql db:
resources:
https://python.langchain.com/docs/integrations/chat/openai/
https://python.langchain.com/docs/use_cases/sql/quickstart/
https://database.guide/2-sample-databases-sqlite/
Run:
> sqlite3 Chinook.db
> .read Chinook_Sqlite.sql
to test:
SELECT * FROM Artist LIMIT 10;

to test codes run:
> python test_agent.py
> python test_chaining.py