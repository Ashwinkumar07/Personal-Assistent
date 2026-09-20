import unittest
import numpy as np
from voice.vad import VoiceActivityDetector
from voice.tts import TextToSpeech

class TestVoiceComponents(unittest.TestCase):
    def test_vad_silence_trimming(self):
        vad = VoiceActivityDetector()
        silence = np.zeros(16000, dtype=np.float32)
        trimmed = vad.trim_silence(silence)
        self.assertEqual(len(trimmed), 0)

    def test_vad_energy_detection(self):
        vad = VoiceActivityDetector()
        loud_chunk = np.ones(480, dtype=np.float32) * 0.5
        self.assertTrue(vad.is_speech_energy(loud_chunk))

        silent_chunk = np.zeros(480, dtype=np.float32)
        self.assertFalse(vad.is_speech_energy(silent_chunk))

    def test_tts_sentence_splitting(self):
        tts = TextToSpeech()
        text = "Hello there! How can I help you? Let's get started."
        sentences = tts.split_sentences(text)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "Hello there!")
        self.assertEqual(sentences[1], "How can I help you?")
        self.assertEqual(sentences[2], "Let's get started.")

if __name__ == "__main__":
    unittest.main()
