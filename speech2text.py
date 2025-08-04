import io
from google.cloud import speech
from pydub import AudioSegment


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