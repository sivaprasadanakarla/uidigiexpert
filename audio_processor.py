import json
import os
import sys
import time
import traceback

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

import concurrent.futures
import sys
from s2tconcur import process_chunk
from inmeetagent_test import invoke_inmeet_agent


def extract_tone_sentiment(text):
    """Extract tone and sentiment from agent response"""
    import re
    match = re.search(r"Tone:\s*(\w+)\s+Sentiment:\s*(\w+)", text)
    return match.groups() if match else (None, None)


def process_single_chunk(chunk, start_time):
    """Process one audio chunk and return analysis"""
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
        print(f"Chunk processing error: {str(e)}")
        return None


def process_audio_parallel(input_path, chunk_duration_ms, total_chunks):
    """Main processing function with parallel execution"""
    results = []
    try:
        # Verify input file exists with retry
        max_retries = 3
        for attempt in range(max_retries):
            if os.path.exists(input_path):
                break
            time.sleep(0.5 * (attempt + 1))  # Wait longer between retries
        else:
            raise FileNotFoundError(f"Input file not found after {max_retries} attempts: {input_path}")

        # Verify file is readable
        try:
            with open(input_path, 'rb') as test_file:
                test_file.read(100)  # Try reading a small portion
        except IOError as e:
            raise IOError(f"File exists but cannot be read: {input_path}. Error: {str(e)}")

        # Load audio file
        print(f"Loading audio file from {input_path}")
        audio = AudioSegment.from_file(input_path)
        print(f"Successfully loaded {len(audio)}ms of audio")

        # Process chunks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []

            # Create and submit all chunk processing tasks
            for i in range(total_chunks):
                start = i * chunk_duration_ms
                end = min(start + chunk_duration_ms, len(audio))
                chunk = audio[start:end]
                futures.append(executor.submit(process_single_chunk, chunk, start))

            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

    except Exception as e:
        print(f"Audio processing failed: {str(e)}")
        traceback.print_exc()

    # Sort results by start time
    return sorted(results, key=lambda x: x['start'])


if __name__ == "__main__":
    try:
        # Parse command line arguments
        if len(sys.argv) != 4:
            raise ValueError("Usage: python audio_processor.py <audio_path> <chunk_ms> <total_chunks>")

        input_path = sys.argv[1]
        chunk_duration_ms = int(sys.argv[2])
        total_chunks = int(sys.argv[3])

        # Process the audio file
        results = process_audio_parallel(input_path, chunk_duration_ms, total_chunks)

        # Save results to JSON file
        with open("processed_results.json", "w") as f:
            json.dump(results, f)

        print(f"Successfully processed {len(results)} chunks")

    except Exception as e:
        print(f"Fatal error in audio processor: {str(e)}")
        traceback.print_exc()
        # Write empty results on failure
        with open("processed_results.json", "w") as f:
            json.dump([], f)
        sys.exit(1)
