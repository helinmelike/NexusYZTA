from fastapi import APIRouter
from schemas.agent import AgentRequest, AgentResponse
from ai_agent.agent import run_agent

router = APIRouter()

chat_history: list[dict] = []


@router.post("/chat", response_model=AgentResponse)
async def chat(req: AgentRequest):
    global chat_history

    try:
        response = run_agent(req.message, chat_history)
    except Exception:
        return AgentResponse(
            reply="Agent su anda LLM servisine baglanamiyor. Lutfen daha sonra tekrar deneyin."
        )

    chat_history.append({"role": "user", "content": req.message})
    chat_history.append({"role": "assistant", "content": response})

    if len(chat_history) > 20:
        chat_history = chat_history[-20:]

    return AgentResponse(reply=response)


@router.delete("/chat/history")
async def clear_history():
    global chat_history
    chat_history = []
    return {"message": "Konuşma geçmişi temizlendi."}
