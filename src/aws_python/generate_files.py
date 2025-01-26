"""Generate files using the OpenAI API."""

from typing import (
    Literal,
    Tuple,
    Union,
)

from loguru import logger
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

SYSTEM_PROMPT = (
    "You are an autocompletion tool that produces text files given constraints."
)


async def get_text_chat_completion(prompt: str) -> str:
    """Generate a text chat completion from a given prompt."""
    client = AsyncOpenAI()

    response: ChatCompletion = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=100,
        n=1,
    )
    logger.debug(response)
    return response.choices[0].message.content or ""


async def generate_image(prompt: str) -> Union[str, None]:
    """Generate an image from a given prompt."""
    client = AsyncOpenAI()

    image_response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    logger.debug(image_response)
    return image_response.data[0].url or None


async def generate_text_to_speech(
    prompt: str,
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3",
) -> Tuple[bytes, str]:
    """
    Generate text-to-speech audio from a given prompt.

    Returns the audio content as bytes and the MIME type as a string.
    """
    client = AsyncOpenAI()

    audio_response = await client.audio.speech.with_raw_response.create(
        model="tts-1",
        voice="echo",
        input=prompt,
        response_format=response_format,
    )
    logger.debug(audio_response)
    file_content_bytes: bytes = audio_response.content
    file_mime_type: str = audio_response.headers.get("Content-Type")

    return file_content_bytes, file_mime_type
