import json
import os
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
from scipy.spatial.distance import cdist
from pyannote.core import Segment
from pyannote.audio import Audio
import numpy as np
from tqdm import tqdm
from typing import Dict, List, Tuple, TypedDict

from .helper import MultiFileHandler, RTTMLine, read_rttm


class ExistingSpeaker(TypedDict):
    file: str
    diarization: List[RTTMLine]


class VerifyType(TypedDict):
    start: float
    duration: float
    file: str


# ExistingType = Tuple[Union[str, AudioSegment], str, float, float]
ExistingType = Tuple[str, str, float, float]


class MultiSpeakerMapper(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False, model: str = "speechbrain/spkrec-ecapa-voxceleb") -> None:
        super().__init__(data_path, verbose, "diarization",
                         "diarization-map", None, ["rttm"])

        # self.results = []
        self.cached_audio = {}
        self.verify = PretrainedSpeakerEmbedding(model)
        self.diarizations: Dict[str, List[RTTMLine]] = {}
        # ,
        # device=torch.device("cuda"))

    def handler(self, input_file: str, output_file: str, file_idx: int) -> None:
        audio_path = input_file.replace(
            "diarization", "raw_audio_voices").replace(".rttm", ".wav")
        _id, diarization = read_rttm(input_file, False)
        for d in diarization:
            speaker = audio_path+"|"+d["speaker"]
            if speaker not in self.diarizations:
                self.diarizations[speaker] = []
            self.diarizations[speaker].append(d)

    def process(self, threshold: float = 0.2):
        print(f'Found {len(self.diarizations.keys())} speakers')
        speakers = list(self.diarizations.keys())
        output_path = os.path.join(self.output_dir, "map.npy")
        output_path2 = os.path.join(self.output_dir, "map.json")
        if not os.path.isfile(output_path):
            # self.results = []
            embeddings = self.get_embeddings()
            results = self.get_loss_map(embeddings)
            # for speaker in (tq:=tqdm(speakers)):
            #             self.results.append(self.compare_speaker(speaker, speakers,tq))
            results = np.array(results)
            np.save(output_path, results)
        else:
            print(
                f'Mapping {output_path} already exists. Using it for mapping')
            results = np.load(output_path)
        # equalities={}
        equals = []
        for speaker1_idx, row in enumerate(results):
            # speaker1 = speakers[speaker1_idx]
            for speaker2_idx, v in enumerate(row):
                # speaker2_idx = np.argmin(row)
                # speaker2 = speakers[speaker2_idx]
                if results[speaker1_idx][speaker2_idx] < threshold and np.argmin(results[speaker1_idx]) == speaker2_idx:
                    equals.append([speaker1_idx, speaker2_idx])
                    # if speaker1_idx<speaker2_idx:
                    #     print(f'{speaker1_idx} == {speaker2_idx}')
                    # else:
                    #     print(f'{speaker2_idx} == {speaker1_idx}')
                    # if speaker1 not in equalities and speaker2 not in equalities:
                    #     equalities[speaker1] = []
                    # if speaker1 in equalities:
                    #     if speaker2 not in equalities[speaker1]:
                    #         equalities[speaker1].append(speaker2)
                    # else:
                    #     if speaker1 not in equalities[speaker2]:
                    #         equalities[speaker2].append(speaker1)
        used = []
        groups = []
        while len(used) < len(equals):
            current = []
            for idx2, eq2 in enumerate(equals):
                if idx2 not in used:
                    current = eq2
                    used.append(idx2)
                    break
            changes = True
            while changes:
                changes = False
                for idx2, eq2 in enumerate(equals):
                    if idx2 not in used:
                        if eq2[0] in current or eq2[1] in current:
                            # if eq2[0] in current and eq2[1] in current:
                            #     continue
                            if eq2[0] in current:
                                if eq2[1] not in current:
                                    current.append(eq2[1])
                            else:
                                if eq2[0] not in current:
                                    current.append(eq2[0])
                            changes = True
                            used.append(idx2)
            groups.append(current)
        all = []
        for g in groups:
            all.extend(g)
        for idx in range(len(results)):
            if idx not in all:
                groups.append([idx])

        for idx, eq in enumerate(groups):
            print(f'Group {idx}: {len(eq)}')
            print('\n'.join([" - "+str(speakers[e]) for e in eq]))

        total_mapped = 0
        total = len(results)
        for g in groups:
            total_mapped += len(g)
        print(f"Mapped: {total_mapped}, total: {total}")
        assert total == total_mapped
        speaker_mapping = {}
        groups.sort(key=len, reverse=True)
        for idx,group in enumerate(groups):
            speaker=f"speaker-{idx}"
            speaker_mapping[speaker]={}
            sorted_group = sorted(group)
            for entry in sorted_group:
                s = speakers[entry].split("|")
                rel_path = os.path.relpath(s[0], self.input_dir.replace(
                    "diarization", "raw_audio_voices")).replace("\\", "/")
                if rel_path not in speaker_mapping[speaker]:
                    speaker_mapping[speaker][rel_path]=[]
                speaker_mapping[speaker][rel_path].append(s[1])
        with open(output_path2,"w") as f:
            json.dump(speaker_mapping, f, indent=4)
    # def compare_speaker(self, speaker:str, speakers:List[str], tq:tqdm) -> List[float]:
    #     results=[]
    #     speaker_idx = speakers.index(speaker)
    #     for idx, speaker2 in enumerate(speakers):
    #         tq.set_description(str(idx))
    #         if speaker_idx>idx:
    #             results.append(self.results[idx][speaker_idx])
    #         elif speaker==speaker2:
    #             results.append(0.0)
    #         else:
    #             results.append(self.get_speakers_loss(speaker, speaker2))
    #     return results

    # def get_speakers_loss(self, speaker1:str, speaker2:str) -> float:
    #     speaker1_file = speaker1.split("|")[0]
    #     speaker2_file = speaker2.split("|")[0]
    #     speaker1_line = self.diarizations[speaker1][0]
    #     speaker2_line = self.diarizations[speaker2][0]
    #     for line in self.diarizations[speaker1]:
    #         if line["duration"]>speaker1_line["duration"]:
    #             speaker1_line = line
    #     for line in self.diarizations[speaker2]:
    #         if line["duration"] > speaker2_line["duration"]:
    #             speaker2_line = line
    #     return self.verify_speaker(speaker1_line, speaker1_file, speaker2_line, speaker2_file)

    def get_embeddings(self):
        embeddings = {}
        for speaker in tqdm(self.diarizations):
            speaker_file = speaker.split("|")[0]
            speaker_line = self.diarizations[speaker][0]
            for line in self.diarizations[speaker]:
                if line["duration"] > speaker_line["duration"]:
                    speaker_line = line
            embeddings[speaker] = self.get_speaker_embedding(
                speaker_line, speaker_file)
        return embeddings

    def get_loss_map(self, embeddings: Dict[str, float]):
        loss_map = []
        for idx1, speaker1 in enumerate(embeddings):
            line = []
            for idx2, speaker2 in enumerate(embeddings):
                # if idx1 < idx2:
                #     line.append(np.inf)
                if speaker1 == speaker2:
                    line.append(np.inf)
                else:
                    line.append(
                        cdist(embeddings[speaker1], embeddings[speaker2], metric="cosine")[0][0])
            loss_map.append(line)
        return loss_map

    def get_speaker_embedding(self, line: RTTMLine, audio_file: str):
        if audio_file in self.cached_audio:
            file = self.cached_audio[audio_file]
        else:
            new_audio = Audio()(audio_file)
            new_audio = {"waveform": new_audio[0], "sample_rate": new_audio[1]}
            self.cached_audio[audio_file] = new_audio
            file = new_audio
        audio = Audio()
        # extract embedding for a speaker speaking between t=3s and t=6s
        speaker1 = Segment(line["start"], line["start"]+line["duration"])
        waveform, sample_rate = audio.crop(file, speaker1)
        return self.verify(waveform[None])

    # def verify_speaker(self, new: RTTMLine, new_file: str, old: RTTMLine, old_file:str) -> float:
    #     embedding1 = self.get_speaker_embedding(new, new_file)
    #     embedding2 = self.get_speaker_embedding(old, old_file)
    #     # compare embeddings using "cosine" distance
    #     return cdist(embedding1, embedding2, metric="cosine")[0][0]
