from app.config.settings import get_settings


def get_chat_model():
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, timeout=20, max_retries=1)


def grounded_completion(system_prompt: str, user_content: str) -> str | None:
    model = get_chat_model()
    if model is None:
        return None
    try:
        response = model.invoke([("system", system_prompt), ("human", user_content)])
        return str(response.content)
    except Exception:
        return None
