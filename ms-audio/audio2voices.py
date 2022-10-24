from pyannote.audio import Pipeline
import os
from typing import Any, TypedDict, Tuple

from .helper import MultiFileHandler, read_rttm


class DiarizationTurn(TypedDict):
    start: float
    end: float


DiarizationTrack = Tuple[DiarizationTurn, Any, str]


class MultiDetector(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False, model: str = "pyannote/speaker-diarization") -> None:
        super().__init__(data_path, verbose, "raw_audio_voices",
                         "diarization", "rttm", ["wav"])
        self.pipeline = Pipeline.from_pretrained(model)

    def handler(self, input_file: str, output_file: str, file_idx: int) -> None:
        uri, audio = os.path.split(input_file)
        file_identifier = {'uri': audio.replace(" ", "_"), 'audio': input_file}
        diarization = self.pipeline(file_identifier)
        # with open(output_file, 'w') as f:
        #     json.dump(result, f, indent=4)
        with open(output_file, "w") as rttm:
            diarization.write_rttm(rttm)
        _id, diarization = read_rttm(output_file)
        # speakers = []
        # for d in diarization:
        #     if d["speaker"] not in speakers:
        #         speakers.append(d["speaker"])
        # overwrite: OverwriteType = {"overwrite": [], "rename": speakers}
        # overwrite_path = output_file.replace(".rttm", ".json")
        # with open(overwrite_path, "w") as f:
        #     json.dump(overwrite, f, indent=4)
