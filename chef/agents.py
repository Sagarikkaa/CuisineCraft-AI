"""
AI Agent Definitions — Multi-Agent Culinary Pipeline

Agent 1: Sous-Chef (Recipe Generation) — gemini-2.5-flash with Google Search Grounding
Agent 2: Nutritionist (Analysis) — gemini-2.5-flash
Agent 3: Narrator (TTS) — gemini-2.5-flash-preview-tts with "Kore" voice
"""
import os
import struct
from google import genai
from google.genai import types


def _get_client():
    """Return an authenticated Gemini client."""
    api_key = os.getenv('GEMINI_API_KEY', '')
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in the environment.")
    return genai.Client(api_key=api_key)


# ── Agent 1: The Sous-Chef ─────────────────────────────────────────
def sous_chef_generate(ingredients: str, cuisine: str) -> str:
    """
    Uses gemini-2.5-flash-preview-09-2025 with Google Search grounding
    to research current culinary trends and generate a structured recipe.
    Returns Markdown-formatted recipe text.
    """
    client = _get_client()

    prompt = f"""You are a world-class sous-chef. A customer has provided
the following ingredients and cuisine preference. Generate a complete,
structured recipe.

**Ingredients available:** {ingredients}
**Cuisine preference:** {cuisine}

Research current culinary trends and ingredient ratios using your search tools.

Your response MUST follow this exact Markdown structure:
## [Recipe Title]

### 🍳 Overview
A 2-3 sentence description of the dish.

### 📋 Ingredients
- List each ingredient with precise measurements

### 👨‍🍳 Instructions
1. Numbered step-by-step instructions
2. Include cooking times and temperatures

### 💡 Chef's Tips
- Any expert tips for perfecting this dish

### ⏱ Total Time
Prep: X min | Cook: Y min | Total: Z min
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.8,
        ),
    )

    return response.text


# ── Agent 2: The Nutritionist ──────────────────────────────────────
def nutritionist_analyze(recipe_body: str, ingredients: str) -> str:
    """
    Uses gemini-2.5-flash-preview-09-2025 to analyze the recipe
    for macro-nutrients and dietary warnings.
    Returns a concise text-based nutritional summary.
    """
    client = _get_client()

    prompt = f"""You are an expert nutritionist. Analyze the following recipe
and its ingredients. Provide a concise nutritional breakdown.

**Recipe:**
{recipe_body}

**Ingredients used:**
{ingredients}

Your response MUST follow this structure:

## 📊 Nutritional Breakdown (Per Serving)

| Nutrient | Amount |
|----------|--------|
| Calories | X kcal |
| Protein  | X g    |
| Total Fat| X g    |
| Carbs    | X g    |
| Fiber    | X g    |
| Sugar    | X g    |
| Sodium   | X mg   |

## ⚠️ Dietary Warnings
List any allergens, dietary concerns, or health notes.

## ✅ Health Benefits
List key nutritional benefits of this meal.

## 🥗 Healthier Alternatives
Suggest 2-3 ingredient swaps to make this recipe healthier.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
        ),
    )

    return response.text


# ── Agent 3: The Narrator ─────────────────────────────────────────
def narrator_synthesize(text: str) -> bytes:
    """
    Uses gemini-2.5-flash-preview-tts with the "Kore" voice
    to convert text into spoken audio.
    Returns raw signed-16-bit PCM audio data.
    """
    client = _get_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Kore",
                    )
                )
            ),
        ),
    )

    # Collect raw PCM bytes from the response
    pcm_data = b""
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            pcm_data += part.inline_data.data

    return pcm_data


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, num_channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """
    Wraps raw PCM data in a RIFF/WAVE header for server-side WAV file creation.
    """
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data)
    chunk_size = 36 + data_size

    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        chunk_size,
        b'WAVE',
        b'fmt ',
        16,                 # Subchunk1Size (PCM)
        1,                  # AudioFormat (PCM = 1)
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        data_size,
    )

    return header + pcm_data
