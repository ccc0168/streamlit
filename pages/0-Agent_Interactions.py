import sounddevice as sd
import soundfile as sf
import streamlit as st
import os
from components.selectors import (
    agent_selection,
    conversation_selection,
    chain_selection,
    prompt_options,
    prompt_selection,
)
from ApiClient import ApiClient
from components.docs import agixt_docs, predefined_injection_variables
import time

st.set_page_config(
    page_title="Agent Interactions",
    page_icon=":speech_balloon:",
    layout="wide",
)


def record_audio(filename="recording.wav", duration=5):
    filename = os.path.join(os.getcwd(), "WORKSPACE", filename)
    samplerate = 44100
    data = sd.rec(frames=duration * samplerate, samplerate=samplerate, channels=1)
    sd.wait()
    sf.write(filename, data=data, samplerate=samplerate)
    st.success(f"Recording saved as '{filename}'")
    return filename


agixt_docs()

st.header("Agent Interactions")
show_injection_var_docs = st.checkbox("Show Prompt Injection Variable Documentation")
if show_injection_var_docs:
    predefined_injection_variables()
try:
    with open(os.path.join("session.txt"), "r") as f:
        agent_name = f.read().strip()
except:
    agent_name = "OpenAI"
st.session_state["conversation"] = conversation_selection(agent_name=agent_name)
mode = st.selectbox(
    "Select Agent Interaction Mode", ["Chat", "Chains", "Prompt", "Instruct"]
)

agent_name = agent_selection() if mode != "Chains" else ""

if mode == "Chat" or mode == "Instruct":
    args = prompt_options()
    args["user_input"] = st.text_area("User Input")
    args["prompt_name"] = "Chat" if mode != "Instruct" else "instruct"
if mode == "Prompt":
    args = prompt_selection()

if mode != "Chains":
    if st.button("Send"):
        args["conversation_name"] = st.session_state["conversation"]
        with st.spinner("Thinking, please wait..."):
            response = ApiClient.prompt_agent(
                agent_name=agent_name,
                prompt_name=args["prompt_name"],
                prompt_args=args,
            )
            if response:
                st.experimental_rerun()
    if st.button("Record Audio to Send"):
        duration = st.slider(
            "Select recording duration in seconds", min_value=1, max_value=30, value=5
        )
        # filename = timestamp_recording.wav
        filename = f"{str(int(time.time()))}_recording.wav"
        filename = record_audio(filename=filename, duration=duration)
        audio_file = open(filename, "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/wav")
        args["conversation_name"] = st.session_state["conversation"]
        # Need to do API call to convert from audio to text
        with st.spinner("Translating audio to text, please wait..."):
            text = ApiClient.execute_command(
                agent_name=agent_name,
                command_name="Read Audio from File",
                command_args={"filename": filename},
            )
            st.success(f"Audio translated to text: '{text}'")
            args["user_input"] = text
            with st.spinner("Thinking, please wait..."):
                response = ApiClient.prompt_agent(
                    agent_name=agent_name,
                    prompt_name=args["prompt_name"],
                    prompt_args=args,
                )
                if response:
                    st.experimental_rerun()


if mode == "Chains":
    chain_names = ApiClient.get_chains()
    agent_override = st.checkbox("Override Agent")
    if agent_override:
        agent_name = agent_selection()
    else:
        agent_name = ""
    advanced_options = st.checkbox("Show Advanced Options")
    if advanced_options:
        single_step = st.checkbox("Run a Single Step")
        if single_step:
            from_step = st.number_input("Step Number to Run", min_value=1, value=1)
            all_responses = False
        else:
            from_step = st.number_input("Start from Step", min_value=1, value=1)
            all_responses = st.checkbox(
                "Show All Responses (If not checked, you will only be shown the last step's response in the chain when done.)"
            )
    else:
        single_step = False
        from_step = 1
        all_responses = False
    args = chain_selection()
    args["conversation_name"] = st.session_state["conversation"]
    chain_name = args["chain"] if "chain" in args else ""
    user_input = args["input"] if "input" in args else ""
    if single_step:
        if st.button("Run Chain Step"):
            if chain_name:
                responses = ApiClient.run_chain_step(
                    chain_name=chain_name,
                    user_input=user_input,
                    agent_name=agent_name,
                    step_number=from_step,
                    chain_args=args,
                )
                st.success(f"Chain '{chain_name}' executed.")
                st.write(responses)
            else:
                st.error("Chain name is required.")
    else:
        if st.button("Run Chain"):
            if chain_name:
                responses = ApiClient.run_chain(
                    chain_name=chain_name,
                    user_input=user_input,
                    agent_name=agent_name,
                    all_responses=all_responses,
                    from_step=from_step,
                    chain_args=args,
                )
                st.success(f"Chain '{chain_name}' executed.")
                st.write(responses)
            else:
                st.error("Chain name is required.")