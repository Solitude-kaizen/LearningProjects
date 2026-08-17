import os

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI


load_dotenv()


def get_groq_api_key():
    return os.getenv("GROQ_API_KEY")


def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")


def generate_groq_response(system_prompt, user_message):
    api_key = get_groq_api_key()

    if not api_key:
        return "Groq API key is not configured yet."

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
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

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-5.6",
        instructions=system_prompt,
        input=user_message,
    )

    return response.output_text


def generate_response(system_prompt, user_message):
    return generate_groq_response(
        system_prompt,
        user_message,
    )