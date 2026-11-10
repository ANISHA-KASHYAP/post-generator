"""Streamlit app: generate LinkedIn posts with Groq or a local Ollama model."""

import os

import streamlit as st

from ollama_client import OllamaError, generate_post
from prompts import ANGLES, LENGTHS, TONES, build_prompt

MODEL = "llama3.2:3b"
GROQ_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]


class AskError(Exception):
    """Raised when neither Groq nor Ollama can generate a post."""


def get_groq_key():
    """Return GROQ_API_KEY from environment or Streamlit secrets, if present."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key

    # st.secrets may not exist locally, so we handle that safely.
    try:
        key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return None

    return key.strip() if key else None


def ask_llama(prompt, temperature=0.8):
    """Use Groq when a key exists, otherwise fall back to local Ollama."""
    groq_key = get_groq_key()

    if groq_key:
        # Import only when needed, so local Ollama still works without groq.
        try:
            from groq import Groq, NotFoundError
        except ImportError as error:
            raise AskError(
                "Groq library is not installed. Run `pip install groq`."
            ) from error

        client = Groq(api_key=groq_key)
        last_error = None

        for model_name in GROQ_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_completion_tokens=2000,
                    reasoning_effort="low",
                )
                content = response.choices[0].message.content
                if content and content.strip():
                    return content.strip()
                # Empty or None content means this model failed; try the next one.
                last_error = AskError("Groq returned an empty response.")
            except NotFoundError as error:
                # Model unavailable? Try the next model in the list.
                last_error = error
            except Exception as error:
                raise AskError(f"Groq error: {error}") from error

        raise AskError(f"Groq models are not available: {last_error}")

    # No Groq key: use the local Ollama model.
    try:
        return generate_post(prompt, model=MODEL, temperature=temperature)
    except OllamaError as error:
        raise AskError(
            f"{error} If this app is online, add GROQ_API_KEY to Streamlit secrets."
        ) from error


st.set_page_config(page_title="LinkedIn Post Generator", layout="centered")

st.title("LinkedIn Post Generator")
st.caption("Uses Groq on Streamlit Cloud, or local Ollama when no Groq key is set.")


# ---------- Sidebar: show which backend will be used ----------
with st.sidebar:
    st.header("Backend")
    if get_groq_key():
        st.success("Using Groq (cloud)")
        st.write("Models: `openai/gpt-oss-20b`, then `openai/gpt-oss-120b`")
    else:
        st.info("Using local Ollama")
        st.write(f"Model: `{MODEL}`")
        st.write("Make sure Ollama is running:")
        st.code("ollama serve", language="bash")

    st.divider()
    st.subheader("How to use")
    st.write("1. Fill in the form.")
    st.write("2. Click **Generate 3 posts**.")
    st.write("3. Copy the version you like best.")


# ---------- Input form ----------
with st.form("post_form"):
    topic = st.text_area(
        "Topic",
        placeholder="e.g. Why small teams ship faster than big teams",
        height=100,
    )

    left, right = st.columns(2)
    with left:
        tone = st.selectbox("Tone", TONES)
        length = st.selectbox("Length", list(LENGTHS.keys()), index=1)
    with right:
        audience = st.text_input(
            "Audience",
            placeholder="e.g. startup founders",
        )

    submitted = st.form_submit_button("Generate 3 posts", use_container_width=True)


# ---------- Generate posts when the form is submitted ----------
if submitted:
    if not topic.strip():
        st.warning("Please enter a topic.")
    elif not audience.strip():
        st.warning("Please enter an audience.")
    else:
        posts = []
        progress = st.progress(0, text="Starting...")

        try:
            for index, angle in enumerate(ANGLES):
                prompt = build_prompt(
                    topic=topic.strip(),
                    tone=tone,
                    length=length,
                    audience=audience.strip(),
                    angle=angle,
                )

                with st.spinner(f"Writing variation {index + 1} of {len(ANGLES)}..."):
                    text = ask_llama(
                        prompt,
                        temperature=0.7 + (index * 0.15),
                    )

                posts.append({"angle": angle, "text": text})
                progress.progress(
                    (index + 1) / len(ANGLES),
                    text=f"Finished {index + 1} of {len(ANGLES)}",
                )

            st.session_state["posts"] = posts
        except AskError as error:
            st.error(str(error))
        finally:
            progress.empty()


# ---------- Show the results ----------
saved_posts = st.session_state.get("posts", [])

if saved_posts:
    st.subheader("Your 3 variations")
    st.caption("Hover over a box and click the copy icon in the top-right corner.")

    tabs = st.tabs(
        [f"Variation {i + 1}: {post['angle']}" for i, post in enumerate(saved_posts)]
    )

    for tab, post in zip(tabs, saved_posts):
        with tab:
            # st.code gives us a ready-made copy button for free.
            st.code(post["text"], language=None, wrap_lines=True)
            st.caption(f"{len(post['text'].split())} words")
