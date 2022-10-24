from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter

import os
from typing import Any, Dict, TypedDict, Tuple, cast

from .helper import MultiFileHandler


class DiarizationTurn(TypedDict):
    start: float
    end: float


DiarizationTrack = Tuple[DiarizationTurn, Any, str]


class MultiVoiceExtractor(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False, model: str = 'spleeter:2stems', vocals_only: bool = True) -> None:
        super().__init__(data_path, verbose, "raw_audio",
                         "raw_audio_voices", "wav")
        # Using embedded configuration.
        self.vocals_only = vocals_only
        self.separator = Separator(model)
        self.audio_loader = AudioAdapter.default()

    def handler(self, input_file: str, output_file: str, file_idx: int) -> None:
        waveform, _sample_rate = cast(
            Tuple[Any, int], self.audio_loader.load(input_file))
        prediction = cast(
            Dict[str, Any], self.separator.separate(waveform, input_file))
        output_dir, output_name = os.path.split(output_file)
        if self.vocals_only:
            voice_only = {"vocals": prediction["vocals"]}
            self.separator.save_to_file(
                voice_only, input_file, output_dir, filename_format=output_file)
        else:
            self.separator.save_to_file(
                prediction, input_file, output_dir)
