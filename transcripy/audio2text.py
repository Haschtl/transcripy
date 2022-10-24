import json
from typing import List, Optional
import whisper
from whisper import Whisper

from .helper import MultiFileHandler, WhisperSegment


# def transcribe(model: Whisper, path: str, language: Optional[str] = None) -> DecodingResult:
#     # load audio and pad/trim it to fit 30 seconds
#     audio = whisper.load_audio(path)
#     audio = whisper.pad_or_trim(audio)

#     # make log-Mel spectrogram and move to the same device as the model
#     mel = whisper.log_mel_spectrogram(audio).to(model.device)
#     if language is None:
#         # detect the spoken language
#         _, probs = model.detect_language(mel)
#         language = max(probs, key=probs.get)
#         print(f"Detected language: {language}")
#     # decode the audio
#     options = whisper.DecodingOptions(language=language)
#     result: DecodingResult = whisper.decode(model, mel, options)
#     return result


class MultiTranscriber(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False, model: str = "medium", english_only: bool = False, forceLanguage: Optional[str] = None) -> None:
        super().__init__(data_path, verbose, "raw_audio_voices",
                         "text", "json", ["wav"])
        if english_only:
            model = model+".en"
        self.model: Whisper = whisper.load_model(model)
        self.forceLanguage = forceLanguage
        self.verbose = verbose

    def handler(self, input_file: str, output_file: str, file_idx: int) -> None:
        if self.forceLanguage is None:
            result = self.model.transcribe(input_file)
        else:
            result = self.model.transcribe(
                input_file, verbose=self.verbose, language=self.forceLanguage)
        segments: List[WhisperSegment] = result["segments"]
        language = result["language"]
        text = result["text"]
        with open(output_file, 'w') as f:
            json.dump({"segments": segments, "language": language,
                      "text": text}, f, indent=4)
