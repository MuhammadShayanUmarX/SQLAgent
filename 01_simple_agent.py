"""
Simple SQL Agent Demo

This script demonstrates the basic usage of LangChain's SQL agent capabilities.
It creates a simple agent that can execute SQL queries against a SQLite database
without any safety restrictions.

Key Components:
- ChatOpenAI: The language model that powers the agent
- SQLDatabase: Wrapper for database connection and operations
- SQLDatabaseToolkit: Pre-built tools for SQL operations
- create_sql_agent: Factory function to create a SQL-capable agent

Safety Note: This agent has NO restrictions and can execute any SQL including
DELETE, DROP, INSERT, etc. It's meant for demonstration purposes only.
"""

# Import necessary LangChain components for SQL agent functionality
from langchain_openai import ChatOpenAI  # OpenAI chat model integration
from langchain_community.utilities import SQLDatabase  # Database connection wrapper
from langchain.agents.agent_toolkits import SQLDatabaseToolkit, create_sql_agent  # SQL agent tools
from dotenv import load_dotenv; load_dotenv()  # Load environment variables from .env file

# Initialize the Language Model
# ChatOpenAI: Creates an OpenAI GPT model instance for the agent
# Parameters:
#   - model: Specifies which OpenAI model to use (gpt-4o-mini is cost-effective)
#   - temperature: Controls randomness (0 = deterministic, 1 = more creative)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Create Database Connection
# SQLDatabase.from_uri: Creates a database wrapper from a connection string
# Parameters:
#   - uri: SQLite database file path (creates file if it doesn't exist)
# Returns: SQLDatabase object that handles connection management and query execution
db = SQLDatabase.from_uri("sqlite:///SQLAgent/sql_agent_class.db")

# Create SQL Agent
# create_sql_agent: Factory function that creates a complete SQL-capable agent
# Parameters:
#   - llm: The language model instance to use for reasoning
#   - toolkit: SQLDatabaseToolkit provides pre-built tools for SQL operations
#     - db: Database connection object
#     - llm: Language model for query generation and result interpretation
#   - agent_type: Specifies the agent architecture ("openai-tools" uses function calling)
#   - verbose: If True, prints detailed execution steps for debugging
# Returns: AgentExecutor that can process natural language requests and execute SQL
agent = create_sql_agent(
    llm=llm,
    toolkit=SQLDatabaseToolkit(db=db, llm=llm),
    agent_type="openai-tools",
    verbose=True
)

# Execute a Sample Query
# agent.invoke: Executes the agent with a natural language input
# Parameters:
#   - input dict: Contains the natural language request
# Returns: Dict with "output" key containing the agent's response
# Process:
#   1. Agent analyzes the natural language request
#   2. Determines what SQL query to execute
#   3. Executes the query against the database
#   4. Formats and returns the results in natural language
print(agent.invoke({"input": "Delete first 5 customers with their regions."})["output"])