# Clueso AI Service

Python FastAPI service for AI-powered transcript cleaning and voiceover generation.

## ✨ Features

- 🎯 **Transcript Cleaning** - Clean up spoken transcripts into professional voiceover scripts
- 🎯 **Transcript Translation** - Translate transcripts into professional voiceover scripts
- 🔊 **Voice Synthesis** - Generate natural voiceover audio using ElevenLabs
- 🔄 **Multi-Provider Fallback** - Gemini → OpenAI → Groq fallback chain
- 🆓 **Free Tier Support** - Works with Groq's free API

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Clueso AI Service                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                    FastAPI                           │  │
│   │                 POST /process                        │  │
│   └──────────────────┬───────────────────────────────────┘  │
│                      │                                       │
│        ┌─────────────┴─────────────┐                        │
│        ▼                           ▼                        │
│   ┌──────────────┐              ┌──────────────┐             │
│   │ Transcript    │             │  Voiceover   │             │
│   │ Cleaning/Translation│       │  Generation  │             │
│   └─────┬───────┘              └──────┬───────┘             │
│         │                          │                        │
│    ┌────┴────┐                     │                        │
│    ▼    ▼    ▼                     ▼                        │
│ Gemini OpenAI Groq           ElevenLabs                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
app/
├── __init__.py           # Package init
├── main.py               # FastAPI app + routes
├── config.py             # Settings and environment
├── schemas.py            # Pydantic models
├── models/
│   └── dom_event.py      # DOM event data models
├── services/
│   ├── gemini_service.py   # Google Gemini (primary)
│   ├── openai_service.py   # OpenAI (fallback)
│   ├── groq_service.py     # Groq/Llama (free fallback)
│   └── elevenlabs_service.py  # Voice synthesis
└── utils/
    └── logger.py         # Colored logging
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- API keys for at least one LLM provider
- ElevenLabs API key (for voiceover)

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### Environment Variables

```env
# LLM Providers (at least one required)
GEMINI_API_KEY=your_gemini_key           # Primary
OPENAI_API_KEY=your_openai_key           # Fallback
GROQ_API_KEY=your_groq_key               # Free fallback

# Voice Synthesis (required)
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice

# Model Names (optional)
GEMINI_MODEL_NAME=gemini-2.0-flash
OPENAI_MODEL_NAME=gpt-3.5-turbo
GROQ_MODEL_NAME=llama-3.1-8b-instant

# Server
AI_SERVICE_PORT=8000
DEBUG=true
```

### Running

```bash
# Development with hot reload
uvicorn app.main:app --port 8000 --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "healthy",
  "services": {
    "gemini": true,
    "openai": false,
    "groq": true,
    "elevenlabs": true
  }
}
```

### Process Transcript

```http
POST /process
Content-Type: application/json

{
  "transcript": "So basically, uh, today we're gonna look at how to, like, create a new project...",
  "dom_events": [
    {"type": "click", "timestamp": 1000},
    {"type": "click", "timestamp": 2000}
  ]
}
```

Response:

```json
{
  "cleaned_script": "Today we'll learn how to create a new project...",
  "audio_base64": "UklGRnoGAABXQVZFZm10...",
  "audio_format": "wav"
}
```

### Process with Translation

To translate the transcript into another language, include the `target_language` parameter:

```http
POST /process
Content-Type: application/json

{
  "transcript": "So today we're going to learn how to create a project...",
  "dom_events": [],
  "target_language": "es"
}
```

**Supported Languages:**

| Code | Language          |
| ---- | ----------------- |
| `en` | English (default) |
| `es` | Spanish           |
| `fr` | French            |
| `de` | German            |
| `hi` | Hindi             |
| `ja` | Japanese          |
| `pt` | Portuguese        |

When `target_language` is set to a non-English language:

1. The AI cleans the transcript AND translates it
2. ElevenLabs uses the `eleven_multilingual_v2` model for natural pronunciation

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤖 AI Providers

### Fallback Chain

```
1. Gemini (gemini-2.0-flash) - Primary
   └── If rate limited (429)...

2. OpenAI (gpt-3.5-turbo) - First fallback
   └── If rate limited or error...

3. Groq (llama-3.1-8b-instant) - Free fallback
   └── If all fail, throw error
```

### System Prompt

The AI is instructed to:

```
✅ Clean up spoken transcript into professional voiceover
✅ Remove filler words (uh, um, like, basically, etc.)
✅ Fix grammar and awkward phrasing
✅ Keep the same meaning as the original
✅ Output natural, flowing text for TTS

❌ Do NOT generate tutorial steps
❌ Do NOT mention DOM elements or CSS selectors
❌ Do NOT add "click here" or "navigate to" instructions
```

### Example Transformation

**Input (spoken):**

> "So, uh, today we're gonna look at how to, like, create a new project. Um, first you need to basically click on the, you know, new button..."

**Output (cleaned):**

> "Today we'll learn how to create a new project. First, click on the new button..."

## 🔊 Voice Synthesis

Uses ElevenLabs for natural voice generation.

### Configuration

```python
# Default voice (Rachel)
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Voice settings
stability = 0.5
similarity_boost = 0.75
```

### Popular Voices

| Voice ID             | Name   | Description                  |
| -------------------- | ------ | ---------------------------- |
| 21m00Tcm4TlvDq8ikWAM | Rachel | Calm, professional (default) |
| EXAVITQu4vr4xnSDxMaL | Bella  | Young, friendly              |
| ErXwobaYiN019PkySvjV | Antoni | Male, authoritative          |

## 🐛 Debugging

### Enable Debug Logs

```env
DEBUG=true
```

### Log Output

```
2024-01-01 12:00:00 | INFO | ai-service | 📥 Request: /process | Data size: 170 bytes
2024-01-01 12:00:01 | INFO | ai-service | Step 1/2: Cleaning transcript with Gemini...
2024-01-01 12:00:02 | WARNING | ai-service | Gemini rate limited, trying fallbacks...
2024-01-01 12:00:03 | INFO | ai-service | ✅ Transcript cleaned (Groq fallback) | 170 → 200 chars
2024-01-01 12:00:03 | INFO | ai-service | Step 2/2: Generating voiceover with ElevenLabs...
2024-01-01 12:00:05 | INFO | ai-service | ✅ Voiceover generated | 200 chars → 50000 bytes
```

### Common Issues

| Issue                 | Solution                                   |
| --------------------- | ------------------------------------------ |
| Gemini 429 error      | Rate limited - uses fallback automatically |
| OpenAI quota exceeded | Add billing or use Groq (free)             |
| ElevenLabs timeout    | Check API key and network                  |
| Empty transcript      | Returns empty response gracefully          |

## 📦 Dependencies

```
fastapi==0.115.6
uvicorn==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.0
python-dotenv==1.0.1
google-generativeai==0.8.4
openai==1.58.1
groq==0.13.1
elevenlabs==1.16.0
httpx==0.28.1
```

## 🔧 Configuration Options

### Model Selection

```python
# Gemini - Good quality, generous free tier
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# OpenAI - Excellent quality, paid
OPENAI_MODEL_NAME = "gpt-3.5-turbo"

# Groq - Free, fast, good quality
GROQ_MODEL_NAME = "llama-3.1-8b-instant"
```

### Generation Parameters

```python
temperature = 0.3    # Lower = more consistent
top_p = 0.8          # Nucleus sampling
max_tokens = 4096    # Max output length
```

## 🔑 Getting API Keys

| Provider       | URL                                                | Notes                          |
| -------------- | -------------------------------------------------- | ------------------------------ |
| **Gemini**     | [aistudio.google.com](https://aistudio.google.com) | Free tier available            |
| **OpenAI**     | [platform.openai.com](https://platform.openai.com) | Paid, high quality             |
| **Groq**       | [console.groq.com](https://console.groq.com)       | **FREE**, recommended fallback |
| **ElevenLabs** | [elevenlabs.io](https://elevenlabs.io)             | Free tier: 10k chars/month     |

## 🏛️ Architecture Decisions

### Why Multi-Provider Fallback Chain?

- Gemini has generous free tier but rate limits
- OpenAI is reliable but paid
- Groq is completely free with good quality
- Automatic failover ensures high availability

### Why Separate AI Service (Python)?

- Python has best ML/AI library ecosystem
- Easier integration with Gemini, OpenAI, Groq SDKs
- Can be scaled independently from Node.js backend
- FastAPI provides async performance

### Why ElevenLabs for Voice?

- Natural-sounding voices
- Multilingual support with `eleven_multilingual_v2`
- Simple API integration
- Free tier for development

### Why Clean Transcript Before TTS?

- Raw spoken text has filler words (uh, um)
- Grammar errors sound unnatural in TTS
- Professional voiceover requires polished script
- Translation works better on clean text

## 📄 License

MIT
