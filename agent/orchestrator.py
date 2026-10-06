"""Agent orchestrator managing the Groq tool-calling loop and PDF mutation state."""

import json
import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from groq import Groq

from agent.prompts import SYSTEM_PROMPT
from agent.tools import RESUME_TOOLS, execute_tool_call

load_dotenv()


def run_resume_agent(
    user_prompt: str,
    pdf_bytes: bytes,
    api_key: str = None,
    model_name: str = "openai/gpt-oss-120b",
    chat_history: List[Dict[str, str]] = None,
) -> Tuple[str, bytes]:
  """Executes the agentic loop using Groq and tool calling.

  Returns: (final_agent_response_text, updated_pdf_bytes)
  """
  effective_api_key = api_key or os.getenv("GROQ_API_KEY")
  if not effective_api_key:
    return (
        (
            "Error: Groq API key is missing. Please enter it in the sidebar or"
            " your .env file."
        ),
        pdf_bytes,
    )

  client = Groq(api_key=effective_api_key)
  active_model = model_name or os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b"

  # Assemble conversation messages
  messages = [{"role": "system", "content": SYSTEM_PROMPT}]

  if chat_history:
    for msg in chat_history[-4:]:  # Keep recent context
      messages.append({"role": msg["role"], "content": msg["content"]})

  messages.append({"role": "user", "content": user_prompt})

  working_pdf_bytes = pdf_bytes
  max_iterations = 6  # Prevent infinite loops
  iteration = 0

  while iteration < max_iterations:
    iteration += 1

    response = client.chat.completions.create(
        model=active_model,
        messages=messages,
        tools=RESUME_TOOLS,
        tool_choice="auto",
        temperature=0.1,  # Low temperature for deterministic tool arguments
    )

    choice = response.choices[0]
    msg = choice.message

    # If the model does not request any more tools, it is finished
    if not msg.tool_calls:
      return msg.content or "Edit completed successfully.", working_pdf_bytes

    # Append assistant's decision to call tools
    messages.append({
        "role": "assistant",
        "tool_calls": [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ],
    })

    # Execute each tool call requested by Groq
    for tool_call in msg.tool_calls:
      fn_name = tool_call.function.name
      try:
        fn_args = json.loads(tool_call.function.arguments)
      except json.JSONDecodeError:
        fn_args = {}

      # Execute tool against the active PDF bytes
      tool_result, working_pdf_bytes = execute_tool_call(
          tool_name=fn_name,
          arguments=fn_args,
          current_pdf_bytes=working_pdf_bytes,
      )

      # Send tool output back to the LLM
      messages.append({
          "role": "tool",
          "tool_call_id": tool_call.id,
          "content": json.dumps(tool_result),
      })

  return (
      "Reached iteration limit. Edits were partially applied.",
      working_pdf_bytes,
  )