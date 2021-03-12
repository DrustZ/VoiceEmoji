from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
import io

class GoogleSpeechRecognizer(object):
    def __init__(self):
        super(GoogleSpeechRecognizer, self).__init__()
        #you need to put your own google api json here
        self.client = speech_v1.SpeechClient.from_service_account_json("gapiKey.json")
        self.language_code = "en-US"

    def recognize(self, local_file_path):
        """
        Transcribe a short audio file using synchronous speech recognition

        Args:
          local_file_path Path to local audio file, e.g. /path/audio.wav
        """
        
        # Sample rate in Hertz of the audio data sent
        sample_rate_hertz = 16000

        # Encoding of audio data sent. This sample sets this explicitly.
        # This field is optional for FLAC and WAV audio formats.
        encoding = enums.RecognitionConfig.AudioEncoding.FLAC
        config = {
            "language_code": self.language_code,
            "sample_rate_hertz": sample_rate_hertz,
            "encoding": encoding,
        }
        with io.open(local_file_path, "rb") as f:
            content = f.read()
        audio = {"content": content}

        response = self.client.recognize(config, audio)
        for result in response.results:
            # First alternative is the most probable result
            alternative = result.alternatives[0]
            return alternative.transcript

        return None
