
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict, cast
from tqdm import tqdm
import os
import unicodedata
import re


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode(
            'ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def all_files(path: str, filetypes: List[str] = ['mp3', 'aac', 'ogg', 'flac', 'alac', 'wav', 'aiff']
              ) -> List[str]:
    files: List[str] = []
    for filetype in filetypes:
        for file in Path(path).rglob('*.'+filetype):
            files.append(os.path.relpath(file.resolve(), path))

    return files


class MultiFileHandler:
    def __init__(self, data_path: str, verbose: bool, input_dir: str, output_dir: str, output_filetype: Optional[str], filetypes: List[str] = ['mp3', 'aac', 'ogg', 'flac', 'alac', 'wav', 'aiff'], ignore_existing: bool = False) -> None:
        self.input_dir = os.path.join(data_path, input_dir)
        self.output_dir = os.path.join(data_path, output_dir)
        self.files = all_files(self.input_dir, filetypes)
        self.output_filetype = output_filetype
        self.ignore_existing = ignore_existing
        self.verbose=verbose

    def handler(self, input_file: str, output_file: str, idx: int) -> None:
        '''
        Handler for each file defined by class extending MultiFileHandler
        '''
        pass

    def run(self):
        for idx, file in tqdm(enumerate(self.files)):
            if self.output_filetype is not None:
                output_file = os.path.splitext(
                    os.path.join(self.output_dir, file))[0]+'.'+self.output_filetype
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
            else:
                os.makedirs(self.output_dir, exist_ok=True)
                output_file = self.output_dir
            input_file = os.path.join(self.input_dir, file)
            if not self.ignore_existing or not os.path.isfile(output_file):
                self.handler(input_file, output_file, idx)
            else:
                print(f"File exists. Skipping... ({output_file})")


class RTTMLine(TypedDict):
    start: float
    duration: float
    speaker: str


class OverwriteType(TypedDict):
    overwrite: List[Any]
    rename: List[str]


def read_rttm(path: str, load_overwrite: bool = True) -> Tuple[str, List[RTTMLine]]:
    # line = (
    #     f"SPEAKER {output.uri} 1 {s.start:.3f} {s.duration:.3f} "
    #     f"<NA> <NA> {l} <NA> <NA>\n"
    # )
    segments: List[RTTMLine] = []
    uri = ''
    with open(path, 'r') as f:
        for idx, line in enumerate(f):
            line_split = line.split(" ")
            if len(line_split) == 10:
                uri = line_split[1]
                start = float(line_split[3])
                duration = float(line_split[4])
                speaker = line_split[7]
                segments.append(
                    {"start": start, "duration": duration, "speaker": speaker})
            else:
                print(f"Unknown line {idx+1}")
    if load_overwrite:
        overwrite_path = path.replace(".rttm", ".json")
        if os.path.isfile(overwrite_path):
            with open(overwrite_path, "r") as f:
                overwrite: OverwriteType = json.load(f)
            for idx, segment in enumerate(segments):
                speaker_idx = get_speaker_idx(segment['speaker'])
                if speaker_idx < len(overwrite['rename']):
                    segments[idx]['speaker'] = overwrite['rename'][speaker_idx]
    return uri, segments


def get_speaker_idx(speaker: str) -> int:
    sp = speaker.split("_")
    if len(sp) == 2:
        return int(sp[1])
    else:
        return -1


class Segment(TypedDict):
    start: float
    end: float
    text: str


def read_split(path: str) -> Dict[str, List[Segment]]:
    with open(path, "r") as f:
        data = json.load(f)
    return cast(Dict[str, List[Segment]], data)


class WhisperSegment(Segment):
    id: int
    seek: int
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float


class TextObject(TypedDict):
    segments: List[WhisperSegment]
    text: str
    language: str


def read_text(path: str) -> TextObject:
    with open(path, "r") as f:
        data = json.load(f)
    return cast(TextObject, data)
