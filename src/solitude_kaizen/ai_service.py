import os
import requests

from dotenv import load_dotenv
from groq import (
    Groq,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
    AuthenticationError,
    PermissionDeniedError,
    BadRequestError,
)
from openai import OpenAI

last_provider_used = None

GROQ_MODEL = "openai/gpt-oss-20b"
OLLAMA_MODEL = "qwen3:4b"
OPENAI_MODEL = "gpt-5.6"


class ProviderError(Exception):
    def __init__(
        self,
        provider,
        kind,
        message,
        retryable=False,
        fallback_allowed=False,
    ):
        super().__init__(message)

        self.provider = provider
        self.kind = kind
        self.retryable = retryable
        self.fallback_allowed = fallback_allowed


load_dotenv()

def generate_ollama_response(system_prompt, user_message):
    prompt = (
        f"{system_prompt}\n\n"
        f"User: {user_message}\n"
        "Solitude-Kaizen:"
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]

    except Exception as error:
        print("Ollama error:", error)

        return (
            "My local AI service is unavailable right now."
        )


def get_groq_api_key():
    return os.getenv("GROQ_API_KEY")


def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")


def generate_groq_response(system_prompt, user_message):
    api_key = get_groq_api_key()

    if not api_key:
        raise ProviderError(
            provider="groq",
            kind="missing_api_key",
            message="Groq API key is not configured yet.",
            retryable=False,
            fallback_allowed=True,
        )

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        return response.choices[0].message.content

    except APITimeoutError as error:
        raise ProviderError(
            provider="groq",
            kind="timeout",
            message="Groq request timed out.",
            retryable=True,
            fallback_allowed=True
        ) from error

    except APIConnectionError as error:
        raise ProviderError(
            provider="groq",
            kind="connection",
            message="Could not connect to Groq.",
            retryable=True,
            fallback_allowed=True
        ) from error

    except RateLimitError as error:
        raise ProviderError(
            provider="groq",
            kind="rate_limit",
            message="Groq rate limit reached.",
            retryable=True,
            fallback_allowed=True
        ) from error

    except InternalServerError as error:
        raise ProviderError(
            provider="groq",
            kind="server_error",
            message="Groq server error.",
            retryable=True,
            fallback_allowed=True
        ) from error

    except Exception as error:
        print("Groq error:", error)

        return (
            "I am having trouble connecting to my AI service "
            "right now. Please try again in a moment."
        )

def generate_openai_response(system_prompt, user_message):
    api_key = get_openai_api_key()

    if not api_key:
        return "OpenAI API key is not configured yet."

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=system_prompt,
            input=user_message,
        )

        return response.output_text

    except Exception as error:
        print("OpenAI error:", error)

        return (
            "I am having trouble connecting to my AI service "
            "right now. Please try again in a moment."
        )

def get_active_provider():
    return os.getenv("AI_PROVIDER", "groq").strip().lower()

def generate_response(system_prompt, user_message):
    global last_provider_used

    provider = get_active_provider()

    if provider == "groq":
        try:
            groq_response = generate_groq_response(
                system_prompt,
                user_message,
            )

        except ProviderError as error:
            if error.fallback_allowed:
                ollama_response = generate_ollama_response(
                    system_prompt,
                    user_message,
                )

                last_provider_used = "ollama"
                return ollama_response

            raise

        groq_failure_messages = [
            (
                "I am having trouble connecting to my AI service "
                "right now. Please try again in a moment."
            ),
        ]

        if groq_response not in groq_failure_messages:
            last_provider_used = "groq"
            return groq_response

        ollama_response = generate_ollama_response(
            system_prompt,
            user_message,
        )

        last_provider_used = "ollama"
        return ollama_response

    if provider == "ollama":
        last_provider_used = "ollama"

        return generate_ollama_response(
            system_prompt,
            user_message,
        )

    if provider == "openai":
        last_provider_used = "openai"

        return generate_openai_response(
            system_prompt,
            user_message,
        )

    last_provider_used = None
    return "No AI provider is currently configured."

def get_last_provider_used():
    return last_provider_used

def get_provider_info():
    provider = get_active_provider()

    if provider == "groq":
        return {
            "provider": "groq",
            "model": GROQ_MODEL,
            "type": "cloud",
        }

    if provider == "ollama":
        return {
            "provider": "ollama",
            "model": OLLAMA_MODEL,
            "type": "local",
        }

    if provider == "openai":
        return {
            "provider": "openai",
            "model": OPENAI_MODEL,
            "type": "cloud",
        }

    return {
        "provider": provider,
        "model": "unknown",
        "type": "unknown",
    }