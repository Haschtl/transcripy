from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
from scipy.spatial.distance import cdist
from pyannote.core import Segment
from pyannote.audio import Audio
import os
import uuid
import json
from random import sample, shuffle
from typing import Dict, List, Tuple, TypedDict, Union
from pydub import AudioSegment
from pydub.utils import get_player_name
import subprocess
# import torch

from .helper import MultiFileHandler, OverwriteType, RTTMLine, all_files, read_rttm


def play_with_native(seg: AudioSegment) -> None:

    PLAYER = get_player_name()
    # with NamedTemporaryFile("w+b", suffix=".wav") as f:
    tmp_path = os.path.abspath("tmp.wav")
    seg.export(tmp_path, "wav")
    subprocess.call(
        [PLAYER, "-nodisp", "-autoexit", "-hide_banner", tmp_path])
    # sleep(seg.duration_seconds+0.4)
    os.remove(tmp_path)


class ExistingSpeaker(TypedDict):
    file: str
    diarization: List[RTTMLine]


class VerifyType(TypedDict):
    start: float
    duration: float
    file: str


# ExistingType = Tuple[Union[str, AudioSegment], str, float, float]
ExistingType = Tuple[str, str, float, float]


class MultiSpeakerSetter(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False, model: str = "pyannote/speaker-diarization") -> None:
        super().__init__(data_path, verbose, "diarization",
                         "diarization", "json", ["rttm"], ignore_existing=True)
        self.earlier_ms = 200
        self.extra_ms = 500
        self.existing_speakers: Dict[str, Dict[str, List[RTTMLine]]] = {}
        diarization_overwrites = all_files(
            os.path.join(data_path, "diarization"), ["json"])
        for file in diarization_overwrites:
            rttm_path = os.path.join(
                data_path, "diarization", file.replace(".json", ".rttm"))
            audio_path = os.path.join(
                data_path, "raw_audio_voices", file.replace(".json", ".wav"))
            _id, diarization = read_rttm(rttm_path, True)
            with open(os.path.join(data_path, "diarization", file), 'r') as f:
                ow: OverwriteType = json.load(f)
                self.add_diarization_file(diarization, ow, audio_path)
        mapping_path = os.path.join(data_path,"diarization-map","map.json")
        self.speaker_mapping = None
        self.rename_speaker_mapping = {}
        if os.path.isfile(mapping_path):
            with open(mapping_path, "r") as f:
                self.speaker_mapping=json.load(f) 
        # self.pipeline = None
        # self.verify = None
        # if automatic:
        #     from pyannote.audio import Pipeline
        #     # self.pipeline = Pipeline.from_pretrained(model)
        #     self.verify = PretrainedSpeakerEmbedding(
        #         "speechbrain/spkrec-ecapa-voxceleb")
        #     # ,
        #     # device=torch.device("cuda"))

    def add_diarization_file(self, diarization: List[RTTMLine], ow: OverwriteType, audio_path: str) -> None:
        for name in ow["rename"]:
            if name not in self.existing_speakers:
                self.existing_speakers[name] = {}
            if audio_path not in self.existing_speakers[name]:
                self.existing_speakers[name][audio_path] = []
            for d in diarization:
                if d["speaker"] == name:
                    self.existing_speakers[name][audio_path].append(d)

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
        print(
            f"Found {len(unknown_speakers)} unknown speakers: {', '.join(unknown_speakers)}")
        for d in diarization:
            if d["speaker"] in overwrite["rename"]:
                new_speaker = None
                if self.speaker_mapping is not None:
                    rel_path = os.path.relpath(audio_path, self.input_dir.replace(
                        "diarization", "raw_audio_voices")).replace("\\", "/")
                    for speaker in self.speaker_mapping:
                        if rel_path in self.speaker_mapping[speaker]:
                            if d["speaker"] in self.speaker_mapping[speaker][rel_path]:
                                new_speaker = speaker
                t1 = int(d["start"]*1000-self.earlier_ms)
                t2 = int((d["start"]+d["duration"])*1000 +
                         self.extra_ms+self.earlier_ms)
                a: AudioSegment = audio_file[t1:t2]
                # if self.verify is not None:
                #     new_speaker = self.find_speaker(
                #         audio_path, diarization, d["speaker"])
                #     if new_speaker is not None:
                #         print(f"Found existing speaker: {new_speaker}")
                # if self.verify is False:
                if new_speaker is None:
                    print(
                        f'Playing sample of {d["speaker"]}... ({a.duration_seconds:.2f}s)')
                    play_with_native(a)
                    new_speaker = input(
                        f"Enter a new name for '{d['speaker']}'.\nLeave blank to skip.\nExisting speakers: {', '.join(self.existing_speakers.keys())}\nNew name: ")
                else:
                    if new_speaker not in self.rename_speaker_mapping:
                        print(
                            f'Playing sample of {d["speaker"]}... ({a.duration_seconds:.2f}s)')
                        play_with_native(a)
                        new_speaker2 = input(
                            f"Enter a new name for '{d['speaker']}'.\nLeave blank to skip.\nExisting speakers: {', '.join(self.existing_speakers.keys())}\nNew name: ")
                        if new_speaker2 != "":
                            self.rename_speaker_mapping[new_speaker]=new_speaker2
                            new_speaker = new_speaker2
                        else:
                            new_speaker = None
                    else:
                        new_speaker = self.rename_speaker_mapping[new_speaker]

                if new_speaker is not None and new_speaker != "":
                    if new_speaker not in self.existing_speakers:
                        self.existing_speakers[new_speaker] = {input_file: []}
                    overwrite["rename"][overwrite["rename"].index(
                        d["speaker"])] = new_speaker

        self.add_diarization_file(diarization, overwrite, audio_path)
        with open(overwrite_path, "w") as f:
            json.dump(overwrite, f, indent=4)

    def find_speaker(self, audio_file: str, diarization: List[RTTMLine], speaker: str) -> Union[str, None]:
        # if self.pipeline is None:
        #     return None
        speaker_diary: List[RTTMLine] = []
        for line in diarization:
            if line["speaker"] == speaker:
                speaker_diary.append(line)
        highest_first = sorted(
            self.existing_speakers.keys(), key=lambda k: len(self.existing_speakers[k].keys()), reverse=True)
        flat_existing: Dict[str, List[ExistingType]] = {}
        for known_speaker in highest_first:
            flat_existing[known_speaker] = []
            d = self.existing_speakers[known_speaker]
            for filename in d:
                for line in d[filename]:
                    flat_existing[known_speaker].append(
                        (filename, line["speaker"], line["start"], line["duration"]))
        losses = {}
        for new in diarization:
            for known_speaker in flat_existing:
                # print(f"Auto-Check if {speaker} is {known_speaker}")
                losses[known_speaker] = 0.0
                # new = sample(diarization, 1)[0]
                old = sample(flat_existing[known_speaker], 1)[0]
                losses[known_speaker] = self.verify_speaker(
                    {"file": audio_file,
                        "start": new["start"], "duration": new["duration"]},
                    {"file": old[0],
                        "start": old[2], "duration": old[3]},
                )
                # audio, diary, loaded_existing = build_audio_sample(
                #     audio_file, speaker_diary, flat_existing[known_speaker])
                # flat_existing[known_speaker] = loaded_existing
                # # input(audio.duration_seconds)
                # tmp_path = os.path.abspath("tmp.wav")
                # # play_with_native(audio)
                # audio.export(tmp_path, "wav")
                # file_identifier = {'uri': "test", 'audio': tmp_path}
                # new_diary = self.pipeline(file_identifier)
                # os.remove(tmp_path)
                # new_speakers = []
                # for speech_turn, track, new_speaker in new_diary.itertracks(yield_label=True):
                #     # print(f"{speech_turn.start:4.1f} {speech_turn.end:4.1f} {speaker}")
                #     if new_speaker not in new_speakers:
                #         new_speakers.append(new_speaker)
                # print(f"Found speakers: {len(new_speakers)}")
                # confidence[known_speaker] = 1/len(new_speakers)
                # if len(new_speakers) == 1:
                #     return str(known_speaker)
            sortedLosses = sorted(
                losses.keys(), key=lambda k: losses[k], reverse=False)
            if losses[sortedLosses[0]] <= 0.2:
                return sortedLosses[0]
        print("I'm not sure, who this is. Losses:")
        print(
            '\n'.join([f"{k}: {losses[k]:.2f}" for k in sortedLosses]))
        return "speaker-"+uuid.uuid4().hex
        # return None

    def verify_speaker(self, new: VerifyType, old: VerifyType) -> float:
        if self.verify is None:
            return
        audio = Audio()
        # extract embedding for a speaker speaking between t=3s and t=6s
        speaker1 = Segment(new["start"], new["start"]+new["duration"])
        waveform1, sample_rate = audio.crop(new["file"], speaker1)
        embedding1 = self.verify(waveform1[None])

        # extract embedding for a speaker speaking between t=7s and t=12s
        speaker2 = Segment(old["start"], old["start"]+old["duration"])
        waveform2, sample_rate = audio.crop(old["file"], speaker2)
        embedding2 = self.verify(waveform2[None])

        # compare embeddings using "cosine" distance
        return cdist(embedding1, embedding2, metric="cosine")[0][0]


def build_audio_sample(audio_file: AudioSegment, diary: List[RTTMLine], existing: List[ExistingType], min_duration: float = 10.0, min_segments: int = 4) -> Tuple[AudioSegment, List[RTTMLine], List[ExistingType]]:
    pre = 0
    post = 0
    crossfade = 0
    shuffle(diary)
    shuffle(existing)
    new_duration = 0.0
    old_duration = 0.0
    new_segments = 0
    old_segments = 0
    old_idx = 0
    new_idx = 0
    idx = 0
    sample = AudioSegment.empty()
    sample_diary: List[RTTMLine] = []
    a: AudioSegment
    while not all([new_duration >= min_duration, old_duration >= min_duration, new_segments >= min_segments, old_segments >= min_segments]):
        idx += 1
        if idx % 2 == 0:
            t1 = int(diary[new_idx]["start"]*1000-pre)
            t2 = int((diary[new_idx]["start"]+diary[new_idx]
                     ["duration"])*1000+post+pre)
            a = audio_file[t1:t2]
            speaker = diary[new_idx]["speaker"]
            new_duration += diary[new_idx]["duration"]
            new_segments += 1
            if new_idx+1 < len(diary):
                new_idx += 1
        else:
            if type(existing[old_idx][0]) is str:
                filename = existing[old_idx][0]
                existing_audio = AudioSegment.from_wav(filename)
                existing[old_idx] = (
                    "", existing[old_idx][1], existing[old_idx][2], existing[old_idx][3])
            else:
                existing_audio = existing[old_idx][0]

            old_duration += existing[old_idx][3]
            speaker = existing[old_idx][1]
            old_segments += 1
            t1 = int(existing[old_idx][2]*1000-pre)
            t2 = int((existing[old_idx][2]+existing[old_idx]
                     [3])*1000+post+pre)
            a = existing_audio[t1:t2]
            if old_idx+1 < len(existing):
                old_idx += 1
        sample_diary.append(
            {"start": sample.duration_seconds, "duration": a.duration_seconds, "speaker": speaker})
        sample = sample.append(a, crossfade)
    return sample, sample_diary, existing
