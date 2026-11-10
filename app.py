"""Streamlit app: generate LinkedIn posts with a local Ollama model."""

import streamlit as st

from ollama_client import OllamaError, generate_post, list_models
from prompts import ANGLES, LENGTHS, TONES, build_prompt

MODEL = "llama3.2:3b"

st.set_page_config(page_title="LinkedIn Post Generator", layout="centered")

st.title("LinkedIn Post Generator")
st.caption("Runs fully on your machine with Ollama. No API keys needed.")


# ---------- Sidebar: check that Ollama and the model are ready ----------
with st.sidebar:
    st.header("Ollama status")
    installed_models = list_models()

    if installed_models is None:
        st.error("Ollama is not running.")
        st.write("Start it in a terminal:")
        st.code("ollama serve", language="bash")
    else:
        st.success("Ollama is running.")
        model_names = [name.split(":")[0] for name in installed_models]
        if MODEL.split(":")[0] in model_names:
            st.write(f"Model `{MODEL}` is installed.")
        else:
            st.warning(f"Model `{MODEL}` is not installed.")
            st.code(f"ollama pull {MODEL}", language="bash")

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
                    text = generate_post(
                        prompt,
                        model=MODEL,
                        temperature=0.7 + (index * 0.15),
                    )

                posts.append({"angle": angle, "text": text})
                progress.progress(
                    (index + 1) / len(ANGLES),
                    text=f"Finished {index + 1} of {len(ANGLES)}",
                )

            st.session_state["posts"] = posts
        except OllamaError as error:
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
