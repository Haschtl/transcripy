# Import the necessary packages
import os
from typing import Optional
from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem


def audio_extract_voice(data_path: str, verbose: bool = False, model: Optional[str] = None, vocals_only: bool = True) -> None:
    if model is None:
        model = "spleeter:2stems"
    from .audioPreprocessing import MultiVoiceExtractor
    MultiVoiceExtractor(data_path, verbose=verbose,
                        model=model, vocals_only=vocals_only).run()


def audio_to_text(data_path: str, verbose: bool = False, model: Optional[str] = None, language: Optional[str] = None) -> None:
    if model is None:
        model = "medium"
    from .audio2text import MultiTranscriber
    MultiTranscriber(data_path, verbose=verbose, model=model,
                     forceLanguage=language, english_only=language == "english").run()


def audio_to_voices(data_path: str, verbose: bool = False, model: Optional[str] = None) -> None:
    if model is None:
        model = "pyannote/speaker-diarization"
    from .audio2voices import MultiDetector
    MultiDetector(data_path, verbose=verbose, model=model).run()


def preprocess(data_path: str, verbose: bool = False) -> None:
    from .audio2text import MultiTranscriber
    from .audio2voices import MultiDetector
    MultiTranscriber(data_path, verbose=verbose).run()
    MultiDetector(data_path, verbose=verbose).run()


def set_speakers(data_path: str, verbose: bool = False) -> None:
    from .setSpeakers import MultiSpeakerSetter
    MultiSpeakerSetter(data_path, verbose=verbose).run()

def map_speakers(data_path: str, verbose: bool = False) -> None:
    from .mapSpeakers import MultiSpeakerMapper
    c = MultiSpeakerMapper(data_path, verbose=verbose)
    c.run()
    c.process()

def text_to_splits(data_path: str, verbose: bool = False) -> None:
    from .text2splits import MultiVoiceSplitter
    MultiVoiceSplitter(data_path, verbose=verbose).run()


def transcribe(data_path: str, verbose: bool = False) -> None:
    from .text2splits import MultiVoiceSplitter
    MultiVoiceSplitter(data_path, verbose=verbose, transcribe=True).run()


def viewer(data_path: str, verbose: bool = False) -> None:
    from .viewer import MultiViewer
    MultiViewer(data_path, verbose=verbose).run()


def slice(data_path: str, verbose: bool = False, pre: float = 0, post: float = 0) -> None:
    from .sliceAudio import MultiSlicer
    MultiSlicer(data_path, verbose=verbose, pre=pre *
                1000, post=post*1000).run()


def create_dataset(data_path: str, verbose: bool = False, pre: float = 0, post: float = 0) -> None:
    from .createDataset import DatasetCreator
    speaker = input('Select a speaker name: ')
    c = DatasetCreator(data_path, speaker, verbose=verbose, pre=pre *
                       1000, post=post*1000)
    c.run()
    c.sample_statistics()
    c.process_samples()

def voice_synthesis():
    from .synthesizer import run
    run()


def main():
    data_path = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), "data")
    model = None
    verbose = False
    options = [
        ["Voice extraction", audio_extract_voice, [data_path, verbose, model]],
        ["Speech recognition", audio_to_text, [data_path, verbose, model]],
        ["Diarization (speaker)", audio_to_voices, [
            data_path, verbose, model]],
        ["[Map Speakers]", map_speakers, [data_path, verbose]],
        ["[Assign Speakers]", set_speakers, [data_path, verbose]],
        ["Combine data", text_to_splits, [data_path, verbose]],
        ["  Transcribe", transcribe, [data_path, verbose]],
        ["  Analyse", viewer, [data_path, verbose]],
        ["  Slice WAV", slice, [data_path, verbose]],
        ["  Create dataset", create_dataset, [data_path, verbose]],
        ["Voice Synthesis", voice_synthesis, []],
        # ["Set data-folder",,[data_path, verbose]],
    ]

    # Create the menu
    menu = ConsoleMenu("Transcripy", "Multi-speaker audio transcription\n"+data_path)
    for option in options:
        # A FunctionItem runs a Python function when selected
        function_item = FunctionItem(*option)
        menu.append_item(function_item)

    # Finally, we call show to show the menu and allow the user to interact
    menu.show()


if __name__ == "__main__":
    main()
