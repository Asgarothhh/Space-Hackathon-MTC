# agent.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
from agent.tools import *
import operator
from agent.system_prompt import SYSTEM_PROMPT
from dotenv import load_dotenv

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    project_root: str
    final_specs: dict | None


tools = [list_files,
         read_file,
         search_in_files,
         write_file,
         edit_file,
         analyze_project,
         explain_metrics]

llm = ChatOpenAI(
    model="openai/gpt-5.1-codex-mini",
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
    temperature=0.3,
    max_tokens=2500,
)

llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    project_root = state.get("project_root")
    if project_root:
        sys_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Текущий project_root уже задан: {project_root}\n"
            "Не спрашивай путь к проекту — используй этот. "
            "Все файловые инструменты (list_files, read_file, analyze_project и т.д.) "
            "должны использовать этот путь как корень проекта."
        )
    else:
        sys_content = SYSTEM_PROMPT

    messages = [SystemMessage(content=sys_content)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("agent")
graph.add_conditional_edges("agent", lambda s: "tools" if s["messages"][-1].tool_calls else END)
graph.add_edge("tools", "agent")

app = graph.compile()