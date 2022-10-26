import os
import json
from pydub import AudioSegment
from pydub.playback import play

from .helper import MultiFileHandler, OverwriteType, read_rttm


class MultiSpeakerSetter(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False) -> None:
        super().__init__(data_path, verbose, "diarization",
                         "diarization", "json", ["rttm"])
        self.earlier_ms = 200
        self.extra_ms = 500

    def handler(self, input_file: str, output_file: str, file_idx: int) -> None:
        audio_path = input_file.replace(
            "diarization", "raw_audio_voices").replace(".rttm", ".wav")
        _id, diarization = read_rttm(input_file, False)
        speakers = []
        for d in diarization:
            if d["speaker"] not in speakers:
                speakers.append(d["speaker"])
        overwrite: OverwriteType = {"overwrite": [], "rename": speakers}
        overwrite_path = output_file.replace(".rttm", ".json")
        if os.path.isfile(overwrite_path):
            with open(overwrite_path, "r") as f:
                overwrite = json.load(f)
        audio_file: AudioSegment = AudioSegment.from_wav(audio_path)
        for d in diarization:
            if d["speaker"] in overwrite["rename"]:
                t1 = int(d["start"]*1000-self.earlier_ms)
                t2 = int((d["start"]+d["duration"])*1000 +
                         self.extra_ms+self.earlier_ms)
                a: AudioSegment = audio_file[t1:t2]
                print(f'Playing sample of {d["speaker"]}...')
                play(a)
                new_speaker = input(
                    f"Enter a new name for this speaker. Leave blank to skip. ")
                if new_speaker != "":
                    overwrite["rename"][overwrite["rename"].index(
                        d["speaker"])]
        with open(overwrite_path, "w") as f:
            json.dump(overwrite, f, indent=4)
