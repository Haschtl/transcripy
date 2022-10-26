import os
from typing import List, Optional, TypedDict

from transcripy.text2splits import transcribe
from .helper import MultiFileHandler, Segment, read_split
from pydub import AudioSegment
import numpy as np


class SamplesType(TypedDict):
    filename: str
    samples: List[Segment]


class DatasetCreator(MultiFileHandler):
    def __init__(self, data_path: str, speaker: str, verbose: bool = False, pre: float = 200.0, post: float = 0.0) -> None:
        super().__init__(data_path, verbose, "voice_splits",
                         "output/datasets", None, ["json"])
        self.speaker = speaker
        self.extra_ms = pre
        self.crossfade=int((pre+post)/2)
        self.earlier_ms = post
        self.samples: List[SamplesType] = []

    def handler(self, input_file: str, output_dir: str, file_idx: int) -> None:
        audio_path = input_file.replace(".json", ".wav").replace(
            "voice_splits", "raw_audio_voices")
        splits = read_split(input_file)
        for person in splits:
            if person == self.speaker:
                self.samples.append(
                    {"filename": audio_path, "samples": splits[person]})

    def sample_statistics(self):
        p = []
        d = []
        w = []
        s = []
        for sample in self.samples:
            durations = [s["end"]-s["start"] for s in sample["samples"]]
            words = [len(s["text"].split(" ")) for s in sample["samples"]]
            w.extend(words)
            d.extend(durations)
            s.append(len(sample["samples"]))
            p.append({"num": len(sample["samples"]),
                     "durations": durations, "words": words})
        d = np.array(d)
        w = np.array(w)
        s = np.array(s)
        print(f'''
Speaker {self.speaker}
Total:
 - {len(p)} files  
 - {np.sum(s)} samples
 - {np.sum(w)} words
 - {np.sum(d):.2f}s duration

Per file:
 - {np.sum(s)/len(p):.2f} samples
 - {np.sum(w)/len(p):.2f} words
 - {np.sum(d)/len(p):.2f}s  duration

 Per sample:
 - {np.sum(w)/np.sum(s):.2f} words
 - {np.sum(d)/np.sum(s):.2f}s  duration

        ''')

    def process_samples(self):
        dataset_audio: Optional[AudioSegment] = None
        dataset_text:List[Segment] = []
        audio_output_path = os.path.join(self.output_dir, self.speaker+".wav")
        text_output_path = os.path.join(self.output_dir, self.speaker+".json")
        for file in self.samples:
            audio_file: AudioSegment = AudioSegment.from_wav(
                file["filename"])
            for segment in file["samples"]:
                t1 = int(segment["start"]*1000-self.earlier_ms)
                t2 = int(segment["end"]*1000+self.extra_ms+self.earlier_ms)
                if t1==t2:
                    print("ERROR: Segment is 0s long")
                    continue
                a: AudioSegment = audio_file[t1:t2]
                if dataset_audio is None:
                    text_start=0
                else:
                    text_start = dataset_audio.duration_seconds
                text_end = text_start + \
                    (segment["end"]-segment["start"]) + \
                    (self.extra_ms+self.earlier_ms)/1000
                if dataset_audio is None:
                    dataset_audio = a
                else:
                    dataset_audio=dataset_audio.append(a, self.crossfade)
                dataset_text.append({"end":text_end,"start":text_start,"text":segment["text"]})
        dataset_audio.export(audio_output_path, format="wav")
        transcribe(dataset_text, text_output_path)
