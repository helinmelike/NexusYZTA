import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from ai_agent.tools import all_tools

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
)

llm_with_tools = llm.bind_tools(all_tools)

SYSTEM_PROMPT = """Sen bir kooperatif işletmesinin AI asistanısın. 
Türkçe konuşuyorsun ve kullanıcının iş operasyonlarını yönetmesine yardım ediyorsun.

Yapabileceklerin:
- Ürün ve stok bilgilerini görüntüleme, güncelleme
- Sipariş oluşturma, listeleme, durum güncelleme, iptal etme
- Müşteri bilgilerini sorgulama ve yeni müşteri ekleme
- Kargo takibi ve tahmini teslimat sorgulama
- Verileri Excel dosyasına aktarma

Kurallar:
- Her zaman Türkçe yanıt ver
- Kullanıcının ne yapmak istediğini anla ve doğru tool'u çağır
- Tool sonuçlarını kullanıcıya sade ve anlaşılır şekilde ilet
- Emin olmadığın durumlarda kullanıcıya sor
"""

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def call_llm(state: AgentState) -> AgentState:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


tool_node = ToolNode(all_tools)

graph_builder = StateGraph(AgentState)
graph_builder.add_node("llm", call_llm)
graph_builder.add_node("tools", tool_node)
graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "llm")

agent = graph_builder.compile()


def run_agent(user_message: str, chat_history: list[dict] = None) -> str:
    messages = []

    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))
    result = agent.invoke({"messages": messages})

    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content

    return "Bir hata oluştu, lütfen tekrar deneyin."