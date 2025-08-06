from pydub import AudioSegment
from pydub.utils import which

# Set ffmpeg paths FIRST
AudioSegment.converter = "/usr/local/Cellar/ffmpeg/7.1.1_3/bin/ffmpeg"
AudioSegment.ffprobe = "/usr/local/Cellar/ffmpeg/7.1.1_3/bin/ffprobe"

# Load and export a short audio file
audio = AudioSegment.from_file("/Users/bhavani/CitiWealthHackathon/syntdata/audio/at1.mp3", format="mp3")
audio[:3000].export("/Users/bhavani/CitiWealthHackathon/syntdata/audio/out.wav", format="wav")
print("Conversion done.")
