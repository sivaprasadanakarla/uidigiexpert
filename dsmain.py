import streamlit as st
import os

# Set environment variables before importing pydub
os.environ["PATH"] += os.pathsep + "/usr/local/Cellar/ffmpeg/7.1.1_3/bin"
os.environ["FFMPEG_BINARY"] = "/usr/local/Cellar/ffmpeg/7.1.1_3/bin/ffmpeg"
os.environ["FFPROBE_BINARY"] = "/usr/local/Cellar/ffmpeg/7.1.1_3/bin/ffprobe"
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from pydub import AudioSegment
from gsutil import read_schedule_from_gcs, read_notification_history_from_gcs
from premeet_agent_test import invoke_premeet_agent
from inmeetagent_test import invoke_inmeet_agent
from s2tconcur import process_chunk

# Configure ffmpeg path
AudioSegment.converter = "/usr/local/Cellar/ffmpeg/7.1.1_3/bin/ffmpeg"
AudioSegment.ffprobe = "/usr/local/Cellar/ffmpeg/7.1.1_3/bin/ffprobe"
import re

def extract_tone_sentiment(text):
    import re
    match = re.search(r"Tone:\s*(\w+)\s+Sentiment:\s*(\w+)", text)
    if match:
        return match.group(1), match.group(2)
    else:
        print(f"⚠️ Could not extract tone/sentiment from: {text}")
        return None, None

def get_tone_emoji(tone):
    tone_map = {
        "neutral": "😐",
        "positive": "😊",
        "negative": "😞",
        "angry": "😡",
        "frustrated": "😤",
        "confused": "😕",
        "happy": "😄",
        "persuasive": "🧠",
        "assertive": "💪",
        "apologetic": "🙏",
        "supportive": "🤝"
    }
    if not tone:
        return "😊"
    return tone_map.get(tone.lower(), "😊")


def get_sentiment_emoji(sentiment):
    sentiment_map = {
        "positive": "👍",
        "neutral": "😐",
        "negative": "👎"
    }
    if not sentiment:
        return "😊"
    return sentiment_map.get(sentiment.lower(), "😊")
# Helper: Extract waveform from audio
def get_waveform(audio: AudioSegment):
    samples = np.array(audio.get_array_of_samples())
    if audio.channels == 2:
        samples = samples.reshape((-1, 2)).mean(axis=1)
    return samples

# Helper: Plot waveform with red marker
def plot_waveform(samples, sample_rate, current_time_sec):
    times = np.linspace(0, len(samples)/sample_rate, num=len(samples))
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.plot(times, samples, linewidth=0.5)
    ax.axvline(x=current_time_sec, color='red', linestyle='--')
    ax.set_xlim(0, times[-1])
    ax.set_ylim(-max(abs(samples)), max(abs(samples)))
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Audio Waveform")
    return fig

# Page config
st.set_page_config(page_title="Advisor AI Copilot Dashboard", layout="wide")

# Title
st.markdown("""
    <h1 style='text-align: center; color: #1E3A8A;'>Digital Experts AI Copilot</h1>
    <h4 style='text-align: center; color: gray;'>Empowering advisors with actionable insights and real-time assistance</h4>
""", unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("## Welcome <span style='color:#1E3A8A;'>John Smith</span>", unsafe_allow_html=True)
    st.markdown("You are logged into Common branch")
    st.markdown("**Role:** Wealth Advisor")
    st.markdown("**Region:** APAC")
    st.markdown("Your last access was on 6 August 2025 at 12:29:58 PM")
    st.markdown("---")

    st.markdown("## Today's Meetings")
    bucket_name = "digexpbucket"
    schedule = read_schedule_from_gcs(bucket_name, "meetings.csv")

    for item in schedule:
        st.markdown(f"**{item['time']}** - {item['client']} (Age {item['age']})")

with col2:
    st.markdown("## Pre-Meeting AI Suggestions")
    client_list = ["---Select---"] + [x["client"] for x in schedule]
    selected_client = st.selectbox("Select a client:", client_list)
    if selected_client and selected_client != "---Select---":
        st.info(f"Fetching insights for **{selected_client}**...")
        st.success(invoke_premeet_agent(selected_client))
    st.markdown("---")

    st.markdown("## Always-On  Service Dashboard")
    st.markdown("#### 🧠 Recently Sent Nudges to Clients (Last 7 Days)")

    notifications_df = read_notification_history_from_gcs(bucket_name)
    if not notifications_df.empty:
        for _, row in notifications_df.iterrows():
            st.markdown(f"##### {row.get('notification_sent_date')}: {'📧' if row.get('notification_type') == 'email' else '📩'} {row.get('message_content')}")
    else:
        st.info("No notification history found for the last 7 days.")

with col3:
    st.markdown("## In-Meeting Copilot advisor")
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])

    waveform_plot = st.empty()
    feedback_container = st.container()
    progress_bar = st.progress(0)

    if uploaded_file:
        st.audio(uploaded_file, format="audio/mp3")
        if 'stop_processing' not in st.session_state:
            st.session_state.stop_processing = False

        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ Start Processing"):
                st.session_state.stop_processing = False
                st.info("Processing audio in 2-second chunks...")

        with col2:
            if st.button("🛑 Stop Processing"):
                st.session_state.stop_processing = True


            # Load audio
        audio = AudioSegment.from_file(BytesIO(uploaded_file.getvalue()))

        chunk_duration_ms = 2000  # 2 seconds
        total_chunks = len(audio) // chunk_duration_ms

        progress_bar = st.progress(0)
        transcripts = []
        feedbacks = []
        chunk_placeholder = st.empty()

        for i in range(total_chunks):
            start = i * chunk_duration_ms
            end = start + chunk_duration_ms
            chunk = audio[start:end]
            if st.session_state.stop_processing:
                st.warning("🚫 Processing was stopped by the user.")
                break
                # Simulate processing time
            time.sleep(3)

            # Call your actual STT and LLM functions here
            transcript = process_chunk(chunk)
            feedback = invoke_inmeet_agent(transcript)

            transcripts.append(transcript)
            feedbacks.append(feedback)
            tone, sentiment = extract_tone_sentiment(feedback)
            tone_emoji = get_tone_emoji(tone)
            sentiment_emoji = get_sentiment_emoji(sentiment)

            chunk_placeholder.markdown(f"""
                - **Tone:** `{tone}`  
                  ### {tone_emoji}
                - **Sentiment:** `{sentiment}`  
                  ### {sentiment_emoji}
                """)
            progress_bar.progress((i + 1) / total_chunks)

            #st.success("✅ Done processing all chunks.")



# Footer
st.markdown("""
    <hr style='border: 1px solid #ccc;'>
    <p style='text-align: center; color: #888;'>© 2025 Citibank Digital Experts | Powered by Google Cloud</p>
""", unsafe_allow_html=True)
