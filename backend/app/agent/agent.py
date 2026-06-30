"""
NYU Bites AI Agent — agentic loop using OpenAI tool calling.

Flow:
  1. Build messages list with system prompt (includes current NYC time)
  2. Call GPT-4o with tool schemas
  3. If the model calls tools → execute them → append results → loop
  4. If the model returns plain text → done
  5. Stop after max_iterations to prevent runaway loops
"""
import json
import logging

from openai import AsyncOpenAI, AuthenticationError, BadRequestError, RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import TOOL_HANDLERS, TOOL_SCHEMAS, _nyc_now
from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

# Groq is OpenAI-compatible — same SDK, different base_url + model
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"
OPENAI_MODEL = "gpt-4o"


def _get_client() -> tuple[AsyncOpenAI, str]:
    """Returns (client, model_name). Prefers Groq over OpenAI."""
    global _client
    if settings.groq_api_key:
        if _client is None:
            _client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url=GROQ_BASE_URL,
            )
        return _client, GROQ_MODEL
    # Fallback to OpenAI
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client, OPENAI_MODEL


def _build_system_prompt() -> str:
    now = _nyc_now()
    time_str = now.strftime("%A, %B %d at %I:%M %p (NYC time)")

    return f"""You are NYU Bites, a friendly and knowledgeable assistant for NYU students \
finding restaurants and cafes with student discounts near Washington Square Park, NYC.

Current time: {time_str}

Your job:
- Help students find places to eat that offer verified NYU student discounts
- Always mention the specific discount (e.g. "10% off with your NYU ID")
- Mention whether the place is currently open when relevant
- Keep responses concise and student-friendly — bullet points work well
- If the student mentions their location (or says "near me"), use rank_proximity to sort by distance
- If they ask "is X open?", use check_hours

You have 4 tools available: search_restaurants, filter_by_discount, check_hours, rank_proximity.
Use them in combination when needed. Think step-by-step before picking a tool."""


async def run_agent(user_query: str, db: AsyncSession, max_iterations: int = 6) -> str:
    # Guard: fail fast if neither key is configured
    if not settings.groq_api_key and not settings.openai_api_key:
        return (
            "⚠️ No AI key configured. Add GROQ_API_KEY=gsk_... to your .env file and restart the server."
        )

    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": user_query},
    ]

    client, model = _get_client()

    _groq_retries = 0
    try:
        for iteration in range(max_iterations):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=0.3,
                    parallel_tool_calls=False,
                )
            except BadRequestError as exc:
                # Groq sometimes generates malformed tool calls — retry up to 2 times
                if "tool_use_failed" in str(exc) and _groq_retries < 2:
                    _groq_retries += 1
                    logger.warning("Groq malformed tool call, retry %d", _groq_retries)
                    continue
                raise
            message = response.choices[0].message

            # Model returned a plain-text answer — we're done
            if not message.tool_calls:
                return message.content or "I couldn't find anything for that. Try rephrasing!"

            # Append the assistant's message (contains the tool call requests)
            messages.append(message.model_dump(exclude_unset=True))

            # Execute every tool the model requested in this round
            for tc in message.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)

                logger.info("Agent calling tool: %s(%s)", fn_name, fn_args)

                handler = TOOL_HANDLERS.get(fn_name)
                if handler:
                    try:
                        tool_result = await handler(fn_args, db)
                    except Exception as exc:
                        logger.exception("Tool %s raised an error", fn_name)
                        tool_result = {"error": str(exc)}
                else:
                    tool_result = {"error": f"Unknown tool: {fn_name}"}

                # Append the tool result so the model sees it next round
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_result, default=str),
                })

    except AuthenticationError:
        return "⚠️ Invalid OpenAI API key. Please check your `OPENAI_API_KEY` in `.env`."
    except RateLimitError:
        return "⚠️ OpenAI rate limit hit. Please try again in a moment."
    except Exception as exc:
        logger.exception("Agent loop failed")
        return f"⚠️ Something went wrong: {exc}"

    return "I hit the maximum number of steps. Try a more specific question!"
