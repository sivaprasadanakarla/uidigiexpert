import concurrent.futures
import io
from pydub import AudioSegment
from google.cloud import speech_v1p1beta1 as speech



def speech_to_text_api(audio_chunk: AudioSegment) -> str:
    """
    Transcribes a given audio chunk using the Google Cloud Speech-to-Text API.

    Args:
        audio_chunk (AudioSegment): A pydub AudioSegment object representing a short
                                    chunk of audio (e.g., 2 seconds).

    Returns:
        str: The transcribed text, or an empty string if transcription fails.
    """
    client = speech.SpeechClient()

    # Convert the pydub AudioSegment into raw audio bytes
    with io.BytesIO() as audio_io:
        audio_chunk.export(audio_io, format="wav")
        content = audio_io.getvalue()

    audio = speech.RecognitionAudio(content=content)

    # Configure the request for the API
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=audio_chunk.frame_rate,
        language_code="en-US",  # Change to the appropriate language code if needed
        model="latest_short"  # Recommended model for short audio chunks
    )

    try:
        # Send the audio chunk to the Speech-to-Text API
        response = client.recognize(config=config, audio=audio)

        # The transcription is usually in the first alternative of the first result
        if response.results:
            return response.results[0].alternatives[0].transcript
        else:
            return ""

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return ""

# Your speech_to_text_api and gen_ai_api functions here

def process_chunk(audio_chunk):
    """A worker function that transcribes and analyzes a single chunk."""
    try:
        # 1. Transcribe the chunk
        transcribed_text = speech_to_text_api(audio_chunk)

        return transcribed_text  # Or return the analysis result
    except Exception as e:
        return f"Error processing chunk: {e}"


def process_audio_concurrently(audio_data):
    """Main function to orchestrate concurrent processing."""
    audio = AudioSegment.from_file(io.BytesIO(audio_data))
    chunk_duration_ms = 2000
    chunks = [audio[i:i + chunk_duration_ms] for i in range(0, len(audio), chunk_duration_ms)]

    transcriptions = {}

    # Create a thread pool with a limited number of workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all transcription jobs and map them to their chunk index
        future_to_chunk_index = {
            executor.submit(process_chunk, chunk): i
            for i, chunk in enumerate(chunks)
        }

        # Process the results as they are completed
        for future in concurrent.futures.as_completed(future_to_chunk_index):
            chunk_index = future_to_chunk_index[future]





    # Combine the results in the correct order for final analysis
    final_transcript = " ".join(transcriptions[i] for i in sorted(transcriptions))
    return final_transcript

# You would call this function after the file is uploaded and the start button is pressed
# final_transcript = process_audio_concurrently(uploaded_file.getvalue())