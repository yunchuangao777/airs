from __future__ import annotations

import streamlit as st

from services.ai_recruiter_service import (
    ask_ai_recruiter,
)
from services.permission_service import (
    require_permission,
)


CHAT_STATE_KEY_PREFIX = "ai_recruiter_messages"


def _get_chat_state_key() -> str:
    """Return a separate chat-history key for each user."""
    username = str(
        st.session_state.get("username", "") or ""
    ).strip().lower()

    if not username:
        username = "anonymous"

    return f"{CHAT_STATE_KEY_PREFIX}_{username}"

SUGGESTED_PROMPTS = [
    "Give me a brief overview of current recruitment activity.",
    "Show the hiring pipeline by application status.",
    "Find candidates with at least five years of experience.",
    "Which interview sessions are waiting for evaluation?",
]


def _initialize_chat() -> None:
    chat_state_key = _get_chat_state_key()

    if chat_state_key not in st.session_state:
        st.session_state[chat_state_key] = [
            {
                "role": "assistant",
                "content": (
                    "Hello. I am the AIRS AI Recruiter. "
                    "I can answer questions about candidates, "
                    "jobs, applications, hiring pipelines, "
                    "interviews, and evaluations."
                ),
            }
        ]


def _clear_chat() -> None:
    chat_state_key = _get_chat_state_key()

    st.session_state[chat_state_key] = [
        {
            "role": "assistant",
            "content": (
                "The conversation has been cleared. "
                "What would you like to review?"
            ),
        }
    ]


def _compact_conversation_history(
    messages: list[dict],
    limit: int = 10,
) -> list[dict[str, str]]:
    """
    Send only recent user/assistant messages to the model.

    Tool traces and UI-only metadata are deliberately excluded.
    """
    history = []

    for message in messages[-limit:]:
        role = str(
            message.get("role") or ""
        ).strip()

        content = str(
            message.get("content") or ""
        ).strip()

        if role in {"user", "assistant"} and content:
            history.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    return history


def _render_suggested_prompts() -> str | None:
    st.markdown("### Suggested Questions")

    columns = st.columns(2)

    selected_prompt = None

    for index, prompt in enumerate(
        SUGGESTED_PROMPTS
    ):
        with columns[index % 2]:
            if st.button(
                prompt,
                use_container_width=True,
                key=f"ai_recruiter_prompt_{index}",
            ):
                selected_prompt = prompt

    return selected_prompt


def _render_tool_trace(
    tool_trace: list[dict],
    message_index: int,
) -> None:
    if not tool_trace:
        return

    with st.expander(
        "Data sources used",
        expanded=False,
    ):
        for index, item in enumerate(
            tool_trace,
            start=1,
        ):
            tool_name = str(
                item.get("tool") or "Unknown tool"
            )

            arguments = item.get(
                "arguments",
                {},
            )

            succeeded = bool(
                item.get("ok")
            )

            status_label = (
                "Completed"
                if succeeded
                else "Failed"
            )

            st.markdown(
                f"**{index}. {tool_name}** — "
                f"{status_label}"
            )

            if arguments:
                st.json(
                    arguments,
                    expanded=False,
                )


def _render_chat_history() -> None:
    messages = st.session_state[
        _get_chat_state_key()
    ]

    for index, message in enumerate(
        messages
    ):
        role = message.get(
            "role",
            "assistant",
        )

        with st.chat_message(role):
            st.markdown(
                str(
                    message.get(
                        "content",
                        "",
                    )
                )
            )

            if role == "assistant":
                _render_tool_trace(
                    message.get(
                        "tool_trace",
                        [],
                    ),
                    message_index=index,
                )


def _submit_question(
    question: str,
) -> None:
    clean_question = str(
        question or ""
    ).strip()

    if not clean_question:
        return

    messages = st.session_state[
        _get_chat_state_key()
    ]

    history = _compact_conversation_history(
        messages
    )

    messages.append(
        {
            "role": "user",
            "content": clean_question,
        }
    )

    with st.chat_message("user"):
        st.markdown(clean_question)

    with st.chat_message("assistant"):
        with st.spinner(
            "Reviewing AIRS data..."
        ):
            try:
                result = ask_ai_recruiter(
                    clean_question,
                    conversation_history=history,
                )

                answer = str(
                    result.get("answer") or ""
                ).strip()

                tool_trace = result.get(
                    "tool_trace",
                    [],
                )

                if not answer:
                    answer = (
                        "I could not produce an answer "
                        "from the available AIRS data."
                    )

                st.markdown(answer)

                _render_tool_trace(
                    tool_trace,
                    message_index=len(
                        messages
                    ),
                )

                messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "tool_trace": tool_trace,
                    }
                )

            except Exception as exc:
                error_message = (
                    "The AI Recruiter could not complete "
                    f"the request: {exc}"
                )

                st.error(error_message)

                messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "tool_trace": [],
                    }
                )


def render_ai_recruiter() -> None:
    require_permission(
        "ai_recruiter.ask",
        message=(
            "You do not have permission to use "
            "the AI Recruiter."
        ),
    )

    _initialize_chat()

    st.markdown(
        """
        <style>
        /* AI Recruiter chat input */
        div[data-testid="stChatInput"] {
            border: 2px solid rgba(120, 120, 120, 0.55) !important;
            border-radius: 12px !important;
            background: transparent !important;
            box-shadow:
                0 1px 3px rgba(0, 0, 0, 0.06) !important;
            transition:
                border-color 0.2s ease,
                box-shadow 0.2s ease !important;
        }

        div[data-testid="stChatInput"]:focus-within {
            border-color: #2e7d5a !important;
            box-shadow:
                0 0 0 2px rgba(46, 125, 90, 0.18) !important;
        }

        div[data-testid="stChatInput"]
        div[data-baseweb="textarea"] {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        div[data-testid="stChatInput"] textarea {
            padding-top: 0.7rem !important;
            padding-bottom: 0.7rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    header_col, action_col = st.columns(
        [4, 1]
    )

    # with header_col:

        # st.title("AI Recruiter")

        # st.caption(
            # "Ask questions about candidates, jobs, "
            # "applications, interviews, and evaluations. "
            # "This version is read-only."
        # )

    with action_col:
        st.write("")

        if st.button(
            "Clear Chat",
            use_container_width=True,
            key="clear_ai_recruiter_chat",
        ):
            _clear_chat()
            st.rerun()

    # st.info(
        # "AI Recruiter provides decision support only. "
        # "Review the underlying candidate and interview "
        # "records before making hiring decisions."
    # )

    selected_prompt = _render_suggested_prompts() 

    st.divider()

    _render_chat_history()

    typed_prompt = st.chat_input(
        "Ask the AI Recruiter..."
    )

    question = (
        typed_prompt
        if typed_prompt
        else selected_prompt
    )

    if question:
        _submit_question(question)