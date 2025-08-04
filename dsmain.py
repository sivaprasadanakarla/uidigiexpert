import streamlit as st
from gsutil import read_schedule_from_gcs
from premeet_agent_test import invoke_premeet_agent
import io
from pydub import AudioSegment
from s2tconcur import process_chunk
from inmeetagent_test import invoke_inmeet_agent

# Page configuration
st.set_page_config(page_title="Advisor AI Copilot Dashboard", layout="wide")

# Title
st.markdown("""
    <h1 style='text-align: center; color: #1E3A8A;'>Digital Experts AI Copilot</h1>
    <h4 style='text-align: center; color: gray;'>Empowering advisors with actionable insights and real-time assistance</h4>
""", unsafe_allow_html=True)

# Layout: 3 columns
col1, col2, col3 = st.columns([1, 2, 1])

# --- Column 1: Advisor Info and Schedule ---
with col1:
    st.markdown("**Name:** John Smith")
    st.markdown("**Region:** APAC")
    st.markdown("**Role:** Wealth Advisor")
    st.markdown("---")

    st.markdown("## Today's Meetings")
    bucket_name = "digexpbucket"
    meetings_filename = "meetings.csv"

    schedule = read_schedule_from_gcs(bucket_name, meetings_filename)

    for item in schedule:
        st.markdown(f"**{item['time']}** - {item['client']} (Age {item['age']})")

# --- Column 2: Pre-Meeting Suggestions ---
with col2:
    st.markdown("## Pre-Meeting AI Suggestions")
    # Prepend the list with the default option
    client_list = ["---Select---"] + [x["client"] for x in schedule]
    selected_client = st.selectbox("Select a client:", client_list)


    # This block will now only run if a valid client is selected
    if selected_client and selected_client != "---Select---":
        st.info(f"Fetching insights for **{selected_client}**...")
        st.success(invoke_premeet_agent(selected_client))

   # if st.button("🔍 View Insights"):
   #     st.markdown("## 📑 Past Data Summary")
   #     st.write("Loading summaries from past emails, chats, and call transcripts...")
   #     st.info("- Last email: Query about maturity of existing policy\n- Chat: Concern on rising market volatility\n- Transcript: Mentioned son moving abroad, may affect estate planning")

    st.markdown("### 🧠 Recently sent nudges to Client(Last 7 days)")
    st.markdown("#####  July 22: 📧 New ETF investment opportunity ")
    st.markdown("#####  July 23: 📩 Market commentary shared on health care")
    st.markdown("#####  July 24: 📧 New ETF investment opportunity ")
# --- Column 3: Real-time Call Analysis ---
with col3:
    st.markdown("## In-Meeting Copilot advisor")
    st.markdown("Upload audio file to simulate live client call")
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])

    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/wav')
        # Initialize a button state in the session state
        if 'transcription_started' not in st.session_state:
            st.session_state.transcription_started = False

        col_start, col_end = st.columns(2)

        with col_start:
            start_button = st.button("Start Transcription")

        with col_end:
            end_button = st.button("End Transcription")

        if start_button:
            st.session_state.transcription_started = True

        if end_button:
            st.session_state.transcription_started = False
            st.info("Transcription ended. Final analysis complete.")

        # Logic to process the audio in chunks
        if st.session_state.transcription_started:
            st.info("Transcribing and analyzing audio...")

            # --- Audio Processing Logic ---
            # Read the audio file into memory
            audio_data = io.BytesIO(uploaded_file.getvalue())

            # Use pydub to handle the audio file (install with pip install pydub)
            try:
                if uploaded_file.name.endswith('.mp3'):
                    audio = AudioSegment.from_mp3(audio_data)
                elif uploaded_file.name.endswith('.wav'):
                    audio = AudioSegment.from_wav(audio_data)
                else:
                    st.error("Unsupported audio format.")
                    st.stop()
            except Exception as e:
                st.error(f"Error processing audio file: {e}")
                st.stop()

            # Define chunk duration (in milliseconds)
            chunk_duration_ms = 2000  # 2 seconds

            # Process audio in 2-second chunks
            for i in range(0, len(audio), chunk_duration_ms):
                chunk = audio[i:i + chunk_duration_ms]

                # Simulate a Speech-to-Text API call
                # In a real app, you would send 'chunk' to your API and get the transcription
                response_text = process_chunk(chunk)

                # This is where you would call your STT API and get the transcript
                # For this example, we'll just print a message
                st.write(f"Chunk {i // chunk_duration_ms + 1}: Simulating STT API call...")
                st.success(invoke_inmeet_agent(response_text))
                # To simulate real-time, you could add a short delay
                # import time; time.sleep(2)

            # Simulated final output after "end" is clicked or all chunks are processed
            if not st.session_state.transcription_started:
                st.success("""
                      **Final Transcript:**
                      (Full transcript here)

                      **Final Analysis:**
                      🔹 Client appears concerned about market dip.
                      🔹 Tone: Slightly anxious.
                      🔹 Suggest calming strategies and long-term perspective.
                      """)

    if st.button("🧠 Simulate Real-Time Call"):
        st.markdown("## 📊 Call Analysis Results")
        st.write("Analyzing call data...")
        st.info("""
        - **Sentiment:** Neutral with slight anxiety
        - **Key Topics:** Market volatility, retirement planning
        - **Action Items:** Reassure client, discuss diversification strategies
        """)


# Footer
st.markdown("""
    <hr style='border: 1px solid #ccc;'>
    <p style='text-align: center; color: #888;'>© 2025 Citibank Digital Experts | Powered by Google Cloud</p>
""", unsafe_allow_html=True)
