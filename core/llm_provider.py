import os
from crewai import LLM


def get_llm() -> LLM:
    provider = os.getenv("LLM_PROVIDER", "amd").lower()

    if provider == "amd":
        return LLM(
            model="openai/Meta-Llama-3.1-8B-Instruct",
            base_url=os.getenv("AMD_BASE_URL"),
            api_key=os.getenv("AMD_API_KEY"),
        )

    elif provider == "openai":
        return LLM(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    elif provider == "groq":
        return LLM(
            model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )

    elif provider == "ollama":
        return LLM(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            api_key="ollama",
        )

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")