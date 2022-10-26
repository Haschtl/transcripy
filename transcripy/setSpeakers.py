import os
import json
from pydub import AudioSegment
from pydub.utils import get_player_name
import subprocess

from .helper import MultiFileHandler, OverwriteType, read_rttm

def play_with_native(seg: AudioSegment) -> None:

    PLAYER = get_player_name()
    # with NamedTemporaryFile("w+b", suffix=".wav") as f:
    tmp_path = os.path.abspath("tmp.wav")
    seg.export(tmp_path, "wav")
    subprocess.call(
        [PLAYER, "-nodisp", "-autoexit", "-hide_banner", tmp_path])
    # sleep(seg.duration_seconds+0.4)
    os.remove(tmp_path)

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
        unknown_speakers = []
        for d in diarization:
            if d["speaker"] not in unknown_speakers:
                unknown_speakers.append(d["speaker"])
        print(f"Found {len(unknown_speakers)} unknown speakers: {', '.join(unknown_speakers)}")
        for d in diarization:
            if d["speaker"] in overwrite["rename"]:
                t1 = int(d["start"]*1000-self.earlier_ms)
                t2 = int((d["start"]+d["duration"])*1000 +
                         self.extra_ms+self.earlier_ms)
                a: AudioSegment = audio_file[t1:t2]
                print(f'Playing sample of {d["speaker"]}... ({a.duration_seconds:.2f}s)')
                # a=a.set_frame_rate(48000)
                play_with_native(a)
                new_speaker = input(
                    f"Enter a new name for this speaker. Leave blank to skip. ")
                if new_speaker != "":
                    overwrite["rename"][overwrite["rename"].index(
                        d["speaker"])] = new_speaker
        with open(overwrite_path, "w") as f:
            json.dump(overwrite, f, indent=4)
