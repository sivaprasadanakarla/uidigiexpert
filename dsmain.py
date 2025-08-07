import streamlit as st
import streamlit.components.v1 as components
import os
import time
import concurrent.futures
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import sys
import base64
import tempfile
from functools import partial
import pandas as pd
# Configure FFmpeg paths
ffmpeg_path = "/usr/local/Cellar/ffmpeg/7.1.1_3/bin"
os.environ["PATH"] += os.pathsep + ffmpeg_path
sys.path.append(ffmpeg_path)
os.environ["FFMPEG_PATH"] = f"{ffmpeg_path}/ffmpeg"
os.environ["FFPROBE_PATH"] = f"{ffmpeg_path}/ffprobe"

# Import pydub after setting paths
from pydub import AudioSegment

AudioSegment.converter = f"{ffmpeg_path}/ffmpeg"
AudioSegment.ffprobe = f"{ffmpeg_path}/ffprobe"

# Import other project modules
from gsutil import read_schedule_from_gcs, read_notification_history_from_gcs_new
from premeet_agent_test import invoke_premeet_agent
from inmeetagent_test import invoke_inmeet_agent
from postmeetagent_test import invoke_postmeet_agent
from s2tconcur import process_chunk

# Initialize session state for notifications if not exists
if 'notifications_data' not in st.session_state:
    st.session_state.notifications_data = None

def get_image_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

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

def process_audio_chunk(chunk, start_time, progress_bar, feedback_container):
    """Process a single audio chunk and update UI"""
    try:
        transcript = process_chunk(chunk)
        feedback = invoke_inmeet_agent(transcript)
        tone, sentiment = extract_tone_sentiment(feedback)

        return {
            "start": start_time,
            "end": start_time + len(chunk),
            "transcript": transcript,
            "feedback": feedback,
            "tone": tone,
            "sentiment": sentiment
        }
    except Exception as e:
        st.error(f"Error processing chunk: {e}")
        return None


def parallel_audio_processing(audio, chunk_duration_ms=2000, max_workers=20):
    """Process audio in parallel chunks"""
    total_chunks = len(audio) // chunk_duration_ms + 1
    chunks = [(audio[i * chunk_duration_ms:(i + 1) * chunk_duration_ms], i * chunk_duration_ms)
              for i in range(total_chunks)]

    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for chunk, start in chunks:
            futures.append(executor.submit(
                process_audio_chunk,
                chunk,
                start,
                progress_bar,
                feedback_container
            ))

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            if result:
                results.append(result)
            progress = (i + 1) / total_chunks
            progress_bar.progress(progress)
            status_text.text(f"Processed {i + 1}/{total_chunks} chunks")

    # Sort by start time
    results.sort(key=lambda x: x['start'])
    return results


# Page config and UI setup
st.set_page_config(page_title="Advisor AI Copilot Dashboard", layout="wide")


# Title
st.markdown("""
    <h1 style='text-align: center; color: #1E3A8A;'>Citi Digital Experts</h1>
    <h4 style='text-align: center; color: gray;'>Empowering advisors with actionable insights and real-time assistance</h4>
""", unsafe_allow_html=True)
st.markdown("---")


col1, col2, col3 = st.columns([1, 2, 2])

with col1:
    # Define your HTML div with styling
    welcome_div = """
    <div style='
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    '>
        <h4 style='color: #1E3A8A;'>Welcome John Smith</h4>
        <p>You are logged into Common branch</p>
        <p><strong>Role:</strong> Wealth Advisor</p>
        <p><strong>Region:</strong> APAC</p>
        <hr style='border: 1px solid #ddd;'>
        <h3>Today's Meetings</h3>
        {meetings_content}
    </div>
    """

    # Generate meetings content
    bucket_name = "digexpbuckselfdata"
    schedule = read_schedule_from_gcs(bucket_name, "meetings.csv")
    meetings_content = "<br>".join(
        f"<strong>{item['time']}</strong> - {item['client']} (Age {item['age']})"
        for item in schedule
    )

    # Render the div with dynamic content
    st.markdown(
        welcome_div.format(meetings_content=meetings_content),
        unsafe_allow_html=True
    )

with col2:
    container2 = st.container()
    st.markdown("### Pre-Meeting AI Agent")
    client_list = ["---Select---"] + [x["client"] for x in schedule]
    selected_client = st.selectbox("Select a client:", client_list)
    if selected_client and selected_client != "---Select---":
        st.info(f"Fetching insights for **{selected_client}**...")
        st.success(invoke_premeet_agent(selected_client))
    st.markdown("---")

    st.markdown("### Always-On Service Dashboard")
    st.markdown("#### 🧠 Recently Sent Nudges to Clients (Last 7 Days)")

    # Initialize if not exists
    if 'notifications_data' not in st.session_state:
        st.session_state.notifications_data = None

    # Load notifications if not loaded
    if st.session_state.notifications_data is None:
        with st.spinner("Loading notifications..."):
            st.session_state.notifications_data = read_notification_history_from_gcs_new(bucket_name)

    # Refresh button
    if st.button("🔄 Refresh Notifications"):
        with st.spinner("Refreshing notifications..."):
            st.session_state.notifications_data = read_notification_history_from_gcs_new(bucket_name)

    # Display notifications with proper null checks
    if st.session_state.notifications_data is None:
        st.warning("Notifications data not loaded yet")
    elif isinstance(st.session_state.notifications_data, pd.DataFrame):
        if st.session_state.notifications_data.empty:
            st.info("No notification history found for the last 7 days.")
        else:
            # Convert timestamp to readable date
            st.session_state.notifications_data['notification_date'] = \
                st.session_state.notifications_data['notification_sent_date'].dt.strftime('%Y-%m-%d %H:%M')

            # Display each notification
            for _, row in st.session_state.notifications_data.iterrows():
                icon = "📧" if row.get('notification_type') == 'email' else "📩"
                with st.expander(f"{icon} {row['notification_date']} - {row['client_name']}"):
                    st.markdown(f"**Type:** {row.get('notification_type', 'N/A')}")
                    st.markdown(f"**Message:** {row['message_content']}")
    else:
        st.error("Invalid notifications data format")

with col3:
    container3 = st.container()
    st.markdown("### In-Meeting AI Agent")
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])

    waveform_plot = st.empty()
    feedback_container = st.container()
    summary_container = st.container()

    if uploaded_file:
        # Initialize session state
        if 'audio_data' not in st.session_state:
            st.session_state.audio_data = None
            st.session_state.precomputed_data = None
            st.session_state.playback_active = False
            st.session_state.start_time = 0
            st.session_state.current_chunk = 0
            st.session_state.postmeetresponse = None

        # Load audio using temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            audio = AudioSegment.from_file(tmp_path)
            st.session_state.audio_data = audio
            st.session_state.audio_duration = len(audio) / 1000
            st.audio(tmp_path, format="audio/mp3")

            # Parallel processing button
            if st.button("🔍 Process Audio (20 threads)") and not st.session_state.precomputed_data:
                with st.spinner("Processing audio with 20 parallel threads..."):
                    st.session_state.precomputed_data = parallel_audio_processing(audio)
                    st.success("Audio processing complete!")

            # Playback controls
            if st.session_state.precomputed_data:
                if not st.session_state.playback_active:
                    if st.button("▶️ Start Playback"):
                        st.session_state.playback_active = True
                        st.session_state.start_time = time.time()
                        st.session_state.current_chunk = 0
                else:
                    if st.button("⏸️ Pause Playback"):
                        st.session_state.playback_active = False

                # Real-time display during playback
                if st.session_state.playback_active:
                    elapsed = time.time() - st.session_state.start_time
                    current_chunk = min(int(elapsed // 2), len(st.session_state.precomputed_data) - 1)

                    if current_chunk != st.session_state.current_chunk:
                        st.session_state.current_chunk = current_chunk
                        data = st.session_state.precomputed_data[current_chunk]

                        # Update waveform
                        samples = get_waveform(audio)
                        fig = plot_waveform(samples, audio.frame_rate, elapsed)
                        waveform_plot.pyplot(fig)

                        # Update feedback
                        with feedback_container:
                            st.markdown(f"""
                            **Segment {current_chunk + 1} ({data['start'] // 1000}-{data['end'] // 1000}s)**
                            - **Transcript:** {data['transcript']}
                            - **Tone:** `{data['tone']}` {get_tone_emoji(data['tone'])}
                            - **Sentiment:** `{data['sentiment']}` {get_sentiment_emoji(data['sentiment'])}
                            - **Feedback:** {data['feedback']}
                            """)

                        time.sleep(0.1)
                        st.rerun()

                    # Check if playback complete
                    if elapsed >= st.session_state.audio_duration:
                        st.session_state.playback_active = False
                        st.success("✅ Meeting playback complete!")

                # Add separate button for post-meeting summary
                if st.button("📄 Generate Post-Meeting Summary"):
                    with st.spinner("Generating meeting summary..."):
                        full_transcript = "\n".join([d["transcript"] for d in st.session_state.precomputed_data])
                        st.session_state.postmeetresponse = invoke_postmeet_agent(full_transcript)
                        st.rerun()

            # Display post-meeting summary if available
            if 'postmeetresponse' in st.session_state:
                with summary_container:
                    st.markdown("### Post-Meeting Summary")
                    st.write(st.session_state.postmeetresponse)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

# Footer
st.markdown("""
    <hr style='border: 1px solid #ccc;'>
    <p style='text-align: center; color: #888;'>© 2025 Citibank Digital Experts | Powered by Google Cloud</p>
""", unsafe_allow_html=True)