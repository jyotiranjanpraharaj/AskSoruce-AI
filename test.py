import os
import unittest
from unittest.mock import MagicMock, patch

# Mock environment variable so the client doesn't complain about missing key
os.environ["GROQ_API_KEY"] = "mock_key"

from core.transcriber import transcribe_chunk, transcribe_all

class TestTranscriber(unittest.TestCase):
    @patch("core.transcriber.Groq")
    @patch("core.transcriber.open")
    def test_transcribe_chunk_languages(self, mock_open, mock_groq_class):
        # Setup mocks
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = b"fake audio content"
        
        mock_client.audio.transcriptions.create.return_value.text = "Hello World"
        
        # Test English
        res = transcribe_chunk("dummy_path.wav", language="english")
        self.assertEqual(res, "Hello World")
        mock_client.audio.transcriptions.create.assert_called_with(
            file=("dummy_path.wav", b"fake audio content"),
            model="whisper-large-v3",
            response_format="json",
            language="en"
        )
        
        # Test Hindi
        res = transcribe_chunk("dummy_path.wav", language="hindi")
        mock_client.audio.transcriptions.create.assert_called_with(
            file=("dummy_path.wav", b"fake audio content"),
            model="whisper-large-v3",
            response_format="json",
            language="hi"
        )

        # Test Hinglish
        res = transcribe_chunk("dummy_path.wav", language="hinglish")
        mock_client.audio.transcriptions.create.assert_called_with(
            file=("dummy_path.wav", b"fake audio content"),
            model="whisper-large-v3",
            response_format="json",
            language="hi"
        )

if __name__ == "__main__":
    unittest.main()
