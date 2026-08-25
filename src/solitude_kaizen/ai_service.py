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
from openai import (
    OpenAI,
    APIConnectionError as OpenAIAPIConnectionError,
    APITimeoutError as OpenAIAPITimeoutError,
    RateLimitError as OpenAIRateLimitError,
    InternalServerError as OpenAIInternalServerError,
    AuthenticationError as OpenAIAuthenticationError,
    PermissionDeniedError as OpenAIPermissionDeniedError,
    BadRequestError as OpenAIBadRequestError,
)

last_provider_used = None

GROQ_MODEL = "openai/gpt-oss-20b"
OLLAMA_MODEL = "qwen3:4b"
OPENAI_MODEL = "gpt-5.6"

GROQ_TIMEOUT_SECONDS = 20.0
OPENAI_TIMEOUT_SECONDS = 20.0

VALID_PROVIDERS = {
    "groq",
    "ollama",
    "openai",
}

DEFAULT_PROVIDER = "groq"

AI_UNAVAILABLE_MESSAGE = (
    "All available AI providers are currently unavailable."
)


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

    except requests.exceptions.Timeout as error:
        raise ProviderError(
            provider="ollama",
            kind="timeout",
            message="Ollama request timed out.",
            retryable=True,
            fallback_allowed=False,
        ) from error

    except requests.exceptions.ConnectionError as error:
        raise ProviderError(
            provider="ollama",
            kind="connection",
            message="Could not connect to Ollama.",
            retryable=True,
            fallback_allowed=False,
        ) from error

    except requests.exceptions.HTTPError as error:
        status_code = None

        if error.response is not None:
            status_code = error.response.status_code

        if (
            status_code is not None
            and 500 <= status_code < 600
        ):
            raise ProviderError(
                provider="ollama",
                kind="server_error",
                message="Ollama server error.",
                retryable=True,
                fallback_allowed=False,
            ) from error

        raise ProviderError(
            provider="ollama",
            kind="http_error",
            message="Ollama rejected the request.",
            retryable=False,
            fallback_allowed=False,
        ) from error

    except Exception as error:
        print(
            "Ollama unexpected error:",
            type(error).__name__,
        )

        raise ProviderError(
            provider="ollama",
            kind="unknown",
            message="Unexpected Ollama error.",
            retryable=False,
            fallback_allowed=False,
        ) from error

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
        client = Groq(api_key=api_key, 
                      timeout=GROQ_TIMEOUT_SECONDS,)

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

    except AuthenticationError as error:
        raise ProviderError(
            provider="groq",
            kind="authentication",
            message="Groq authentication failed.",
            retryable=False,
            fallback_allowed=True,
        ) from error

    except PermissionDeniedError as error:
        raise ProviderError(
            provider="groq",
            kind="permission_denied",
            message="Groq permission denied.",
            retryable=False,
            fallback_allowed=True,
        ) from error

    except BadRequestError as error:
        raise ProviderError(
            provider="groq",
            kind="bad_request",
            message="Groq rejected the request.",
            retryable=False,
            fallback_allowed=False,
        ) from error
    
    except Exception as error:
        print(
            "Groq unexpected error:",
            type(error).__name__,
        )

        raise ProviderError(
            provider="groq",
            kind="unknown",
            message="Unexpected Groq error.",
            retryable=False,
            fallback_allowed=False,
        ) from error

def generate_openai_response(system_prompt, user_message):
    api_key = get_openai_api_key()

    if not api_key:
        raise ProviderError(
        provider="openai",
        kind="missing_api_key",
        message="OpenAI API key is not configured yet.",
        retryable=False,
        fallback_allowed=True,
    )

    try:
        client = OpenAI(
    api_key=api_key,
    timeout=OPENAI_TIMEOUT_SECONDS,
    )

        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=system_prompt,
            input=user_message,
        )

        return response.output_text

    except OpenAIAPITimeoutError as error:
        raise ProviderError(
            provider="openai",
            kind="timeout",
            message="OpenAI request timed out.",
            retryable=True,
            fallback_allowed=True,
        ) from error

    except OpenAIAPIConnectionError as error:
        raise ProviderError(
            provider="openai",
            kind="connection",
            message="Could not connect to OpenAI.",
            retryable=True,
            fallback_allowed=True,
        ) from error

    except OpenAIRateLimitError as error:
        raise ProviderError(
            provider="openai",
            kind="rate_limit",
            message="OpenAI rate limit reached.",
            retryable=True,
            fallback_allowed=True,
        ) from error

    except OpenAIInternalServerError as error:
        raise ProviderError(
            provider="openai",
            kind="server_error",
            message="OpenAI server error.",
            retryable=True,
            fallback_allowed=True,
        ) from error

    except OpenAIAuthenticationError as error:
        raise ProviderError(
            provider="openai",
            kind="authentication",
            message="OpenAI authentication failed.",
            retryable=False,
            fallback_allowed=True,
        ) from error

    except OpenAIPermissionDeniedError as error:
        raise ProviderError(
            provider="openai",
            kind="permission_denied",
            message="OpenAI permission denied.",
            retryable=False,
            fallback_allowed=True,
        ) from error

    except OpenAIBadRequestError as error:
        raise ProviderError(
            provider="openai",
            kind="bad_request",
            message="OpenAI rejected the request.",
            retryable=False,
            fallback_allowed=False,
        ) from error

    except Exception as error:
        print(
            "OpenAI unexpected error:",
            type(error).__name__,
        )

        raise ProviderError(
            provider="openai",
            kind="unknown",
            message="Unexpected OpenAI error.",
            retryable=False,
            fallback_allowed=False,
        ) from error

def get_active_provider():
    provider = os.getenv(
        "AI_PROVIDER",
        DEFAULT_PROVIDER,
    ).strip().lower()

    if provider not in VALID_PROVIDERS:
        raise ProviderError(
            provider="config",
            kind="invalid_provider",
            message="Invalid AI provider configuration.",
            retryable=False,
            fallback_allowed=False,
        )

    return provider

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
                try:
                    ollama_response = generate_ollama_response(
                        system_prompt,
                        user_message,
                    )

                except ProviderError as fallback_error:
                    if fallback_error.retryable:
                        last_provider_used = None
                        return AI_UNAVAILABLE_MESSAGE

                    raise

                last_provider_used = "ollama"
                return ollama_response

            raise

        last_provider_used = "groq"
        return groq_response

    if provider == "ollama":
        last_provider_used = "ollama"

        return generate_ollama_response(
            system_prompt,
            user_message,
        )

    if provider == "openai":
        try:
            openai_response = generate_openai_response(
                system_prompt,
                user_message,
            )

        except ProviderError as error:
            if error.fallback_allowed:
                try:
                    ollama_response = generate_ollama_response(
                        system_prompt,
                        user_message,
                    )

                except ProviderError as fallback_error:
                    if fallback_error.retryable:
                        last_provider_used = None
                        return AI_UNAVAILABLE_MESSAGE

                    raise

                last_provider_used = "ollama"
                return ollama_response

            raise

        last_provider_used = "openai"
        return openai_response

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