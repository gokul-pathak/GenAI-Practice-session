from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from dotenv import load_dotenv
import os

load_dotenv()

base_url = os.getenv("BASE_URL_OLLAMA")
system_prompt = os.getenv("EX_PROMPT")

llm = ChatOllama(
    model="kimi-k2.5:cloud",
    base_url=base_url
)

# Store session histories
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Inject system prompt every time
def add_system_message(messages):
    return [SystemMessage(content=system_prompt)] + messages

chain = RunnableLambda(add_system_message) | llm

chat = RunnableWithMessageHistory(
    chain,
    get_session_history
)

while True:
    user_input = input("Ask me anything --> ")

    if user_input.lower() == "exit":
        print("Goodbye 👋")
        break

    response = chat.invoke(
        [HumanMessage(content=user_input)],
        config={"configurable": {"session_id": "default"}}
    )

    print("Your EX:", response.content)
