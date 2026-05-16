# Gyanova v4 — AI Agent Over a Phone Call

**Authors:** [Swaroop Ingavale](https://www.linkedin.com/in/swaroop-ingavale-31142619b/) · [Pradeep Mokashi](https://www.linkedin.com/in/pradeep-mokashi/)

---

## The Problem

Across conflict zones, censored regions, and infrastructure-poor areas, millions of people are cut off from the internet. Data networks are blocked, restricted, or simply unaffordable. Yet these are often the people who need information the most — real-time weather, safety updates, news, the ability to send a message to a loved one.

Smartphones and apps are useless without data. But a basic phone call still works almost everywhere.

---

## The Idea

What if you could call a phone number — a regular voice call, no internet, no app, no smartphone required — and talk to an AI agent?

Ask it the weather. Ask it what's happening in the news. Ask it to send an email on your behalf. Get a spoken answer back, in seconds.

That is Gyanova.

It puts an AI agent on the other end of a phone line. The user needs nothing more than the ability to make a call. All the intelligence, all the data fetching, all the reasoning happens on the server. The phone is just the microphone and speaker.

---

## Who This Is For

- People in conflict zones where internet access is blocked or surveilled
- Communities in remote areas with no mobile data infrastructure
- Regions under government-imposed internet shutdowns
- Anyone with a basic phone and no data plan

---

## How It Works

```
User (basic phone, no internet)
        |
        | regular voice call (PSTN / VoIP)
        |
        ▼
Gyanova Server
        |
        ├── STT (Speech-to-Text) — converts voice to text
        |
        ├── AI Agent (Groq / Llama 4) — understands the query,
        |       breaks it into tasks, decides which tools to call
        |
        ├── Tools (run on server, all internet-side)
        |       ├── web_search    — fetches live information
        |       ├── get_weather   — fetches real-time weather
        |       ├── findDateTime  — timezone-aware date and time
        |       ├── send_email    — sends email on user's behalf
        |       └── translate_text — translates content to user's language
        |
        ├── Final Answer — LLM composes a natural spoken response
        |
        └── TTS (Text-to-Speech) — speaks the answer back to the user
```

The user's device does zero computation and zero data. Everything happens on the server. The voice call is the only channel needed.

---

## Example Interactions

"What is the weather in Kabul today?"
→ Gyanova fetches live weather and reads it back over the call.

"What is happening in the news?"
→ Gyanova searches the web and summarizes current events in speech.

"Send an email to my brother at this address and tell him I am safe."
→ Gyanova composes and sends the email, confirms back over the call.

"What time is it in Toronto?"
→ Gyanova returns the current local time for that timezone.

---

## Technical Stack

| Component | Technology |
|---|---|
| Voice I/O | fastrtc (real-time audio streaming) |
| Speech-to-Text | fastrtc STT model |
| Text-to-Speech | fastrtc TTS model |
| AI Reasoning | Groq API — Llama 4 Scout 17B |
| Web Search | SerpAPI |
| Weather | Weather API |
| Email | SMTP / Gmail |
| Translation | Translation API |
| Self-extending tools | AgentGenerator (LLM-generated tool code) |

---

## Key Design Decisions

**No data required on the user's end.** The entire system is server-side. The phone call is just the audio interface.

**Multi-step task chaining.** A single query like "get the weather in my city and email it to my sister" is automatically broken into dependent subtasks and executed in sequence.

**Self-extending.** New tools can be added by describing them in plain English. The system writes, registers, and integrates the new tool automatically via `agent_generator.py`.

**Dual mode.** Runs in audio mode (phone/voice) or text mode (terminal) depending on the `AUDIO_MODE` environment variable, making development and testing straightforward.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/swarpya/gyanova_v4.git
cd gyanova_v4
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
AUDIO_MODE=true

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 4. Run

```bash
python main.py
```

In audio mode, Gyanova starts listening for incoming voice connections. In text mode, it prompts for a typed query.

---

## Adding a New Tool

Describe what you want in plain English:

```bash
python agent_generator.py "fetch live flight status for a given flight number"
```

Gyanova will write the tool code, register it in `tools/__init__.py`, and update `core/config.py` automatically. The tool is immediately available to the agent.

---

## Vision

Most AI assistants are built for people who already have everything — a smartphone, a data plan, a stable connection. Gyanova is built for everyone else. A phone call is one of the most universally accessible communication channels on the planet. Gyanova puts AI on that channel.

Information should not be a privilege of connectivity.

---

## License

MIT License
