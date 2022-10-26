from genericpath import isfile
import json
import math
import os
from typing import Dict, List, Union
from colorama import init, Fore, Back, Style
from .helper import MultiFileHandler, RTTMLine, Segment, read_rttm, read_text
from pycaption import DFXPWriter, SAMIWriter, SRTWriter, CaptionList, CaptionSet, Caption, CaptionNode
from pycaption.transcript import TranscriptWriter
# Initializes Colorama
init(autoreset=True)


def epow(v: float) -> float:
    if v < 0:
        v = 0.1*v
    return math.pow(math.e, abs(v))


def lin(v: float) -> float:
    if v < 0:
        v = 0.1*v
    return abs(v)


def speaker_style(idx: int) -> str:
    style: str = Style.BRIGHT
    foreIdx = idx % 4
    if foreIdx == 1:
        style += Fore.RED
    elif foreIdx == 2:
        style += Fore.BLUE
    elif foreIdx == 3:
        style += Fore.GREEN
    elif foreIdx == 4:
        style += Fore.CYAN
    elif foreIdx == 5:
        style += Fore.MAGENTA
    else:
        style += Fore.WHITE
    # if idx == 1:
    #     return Style.BRIGHT + Back.GREEN
    return style


def find_nearest_speaker(diarization: List[RTTMLine], start: float, end: float, loss: str = "linear") -> Union[RTTMLine, None]:
    if len(diarization) == 0:
        return None
    if loss == "linear":
        loss_func = lin
    else:
        loss_func = epow
    losses: List[float] = []
    filtered_diarization: List[RTTMLine] = []
    for entry in diarization:
        if len(losses) == 0:
            filtered_diarization.append(entry)
        elif filtered_diarization[-1]["speaker"] != entry["speaker"]:
            filtered_diarization.append(entry)
        else:
            filtered_diarization[-1]["duration"] = entry["start"] + \
                entry["duration"]-filtered_diarization[-1]["start"]
    for entry in filtered_diarization:
        speaker_start = entry["start"]
        speaker_end = entry["start"]+entry["duration"]
        end_loss = loss_func(end-speaker_end)
        start_loss = loss_func(speaker_start-start)
        losses.append(2*start_loss+end_loss)

    min_v = losses[0]
    index = 0
    for i in range(1, len(losses)):
        if losses[i] < min_v:
            min_v = losses[i]
            index = i
    return diarization[index]


def num2str(v: float) -> str:
    return f'{v:.2f}'


class MultiVoiceSplitter(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False, transcribe: bool = False) -> None:
        super().__init__(data_path, verbose, "raw_audio_voices",
                         "voice_splits", "json", ignore_existing=transcribe)
        self.transcribe = transcribe

    def handler(self, input_file: str, output_file: str, file_idx: int) -> None:
        diarization_path = input_file.replace(
            "raw_audio_voices", "diarization").replace(".wav", ".rttm")
        text_path = input_file.replace(
            "raw_audio_voices", "text").replace(".wav", ".json")
        diarization = []
        if not os.path.isfile(text_path):
            print(Back.BLACK+Fore.RED +
                  f"\nWarning!\nNo text '{text_path}' found!.\nRun --audio2text for text-recognition first\n")
            return
        if os.path.isfile(diarization_path):
            _id, diarization = read_rttm(diarization_path)
        else:
            print(Back.BLACK+Fore.RED +
                  f"\nWarning!\nNo diarization '{diarization_path}' found!\nRun --audio2voices for speaker-detection\n")
        text = read_text(text_path)
        # audio = load_audio(input_file)
        # splits=self.find_splits(diarization,text)
        # for split in splits:
        #     # create output_path
        #     # split audio
        #     audio_split = audio
        #     # save audio
        speakers = []
        if diarization is not None:
            for d in diarization:
                if d["speaker"] not in speakers:
                    speakers.append(d["speaker"])
        num_speakers = len(speakers)
        num_diaries = len(diarization)
        num_text_segments = len(text["segments"])
        if self.transcribe:
            print(
                f"\n\n{input_file}\nNumber of diaries: {num_diaries} ({num_speakers} speakers). Number of text-segments: {num_text_segments}")
        # t = 0.0
        # diary_idx = 0
        # text_idx = 0
        splits: Dict[str, List[Segment]] = {}
        last_speaker = ""
        captions: List[Caption] = []
        for segment in text["segments"]:
            speaker = ""
            speaker_line = find_nearest_speaker(
                diarization, segment["start"], segment["end"])
            if speaker_line is not None:
                speaker = speaker_line["speaker"]
                speaker_color = speaker_style(
                    speakers.index(speaker))
                end = max(segment["end"], speaker_line["start"] +
                          speaker_line["duration"])
                start = max(segment["start"], speaker_line["start"])
                if self.transcribe and speaker != last_speaker:
                    print(
                        speaker_color+f'================ {speaker}')
            else:
                speaker_color = speaker_style(0)
                end = segment["end"]
                start = segment["start"]
            print_text = speaker_color + f'{segment["text"]}'
            # print(
            #     speaker_color+ f'{segment["text"]}',end="")
            if self.transcribe:
                print('{:<100} {:>6} : {:>6}'.format(
                    print_text, num2str(start), num2str(end)))
                nodes: List[CaptionNode]
                if speaker != "":
                    nodes = [CaptionNode(
                        CaptionNode.TEXT, content=speaker+": "+segment["text"])]
                else:
                    nodes = [CaptionNode(
                        CaptionNode.TEXT, content=segment["text"])]
                captions.append(Caption(start*1000000, end*1000000, nodes))
            last_speaker = speaker

            if last_speaker not in splits:
                splits[last_speaker] = []
            splits[last_speaker].append(
                {"start": segment["start"], "end": segment["end"], "text": segment["text"]})
        if not self.transcribe:
            with open(output_file, "w") as f:
                json.dump(splits, f, indent=4)
        else:
            captionSet = CaptionSet({text["language"]: CaptionList(captions)})
            output_file = output_file.replace(
                "voice_splits", os.sep.join(['output', 'transcripts']))
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            srt = SRTWriter().write(captionSet)
            sami = SAMIWriter().write(captionSet)
            dfx = DFXPWriter().write(captionSet)
            transcript = TranscriptWriter().write(captionSet)
            txt_transcript = f"# Language: {text['language']}"
            for c in captions:
                txt_transcript += f"\n{c.format_start()} - {c.format_end()}: {c.get_text()}"
            try:
                with open(output_file.replace(".json", ".srt"), "w") as f:
                    f.write(srt)
            except Exception:
                pass
            try:
                with open(output_file.replace(".json", ".sami"), "w") as f:
                    f.write(sami)
            except Exception:
                pass
            try:
                with open(output_file.replace(".json", ".dfx"), "w") as f:
                    f.write(dfx)
            except Exception:
                pass
            try:
                with open(output_file.replace(".json", ".transc"), "w") as f:
                    f.write(transcript)
            except Exception:
                pass
            try:
                with open(output_file.replace(".json", ".txt"), "w") as f:
                    f.write(txt_transcript)
            except Exception:
                pass


def transcribe(segments: List[Segment], output_path:str, language: str = "english") -> None:
    splits: Dict[str, List[Segment]] = {}
    last_speaker = ""
    captions: List[Caption] = []
    for segment in segments:
        end = segment["end"]
        start = segment["start"]
        nodes = [CaptionNode(
            CaptionNode.TEXT, content=segment["text"])]
        captions.append(Caption(start*1000000, end*1000000, nodes))

        if last_speaker not in splits:
            splits[last_speaker] = []
        splits[last_speaker].append(
            {"start": segment["start"], "end": segment["end"], "text": segment["text"]})
    captionSet = CaptionSet({language: CaptionList(captions)})
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    srt = SRTWriter().write(captionSet)
    sami = SAMIWriter().write(captionSet)
    dfx = DFXPWriter().write(captionSet)
    transcript = TranscriptWriter().write(captionSet)
    txt_transcript = f"# Language: {language}"
    for c in captions:
        txt_transcript += f"\n{c.format_start()} - {c.format_end()}: {c.get_text()}"
    try:
        with open(output_path.replace(".json", ".srt"), "w") as f:
            f.write(srt)
    except Exception:
        pass
    try:
        with open(output_path.replace(".json", ".sami"), "w") as f:
            f.write(sami)
    except Exception:
        pass
    try:
        with open(output_path.replace(".json", ".dfx"), "w") as f:
            f.write(dfx)
    except Exception:
        pass
    try:
        with open(output_path.replace(".json", ".transc"), "w") as f:
            f.write(transcript)
    except Exception:
        pass
    try:
        with open(output_path.replace(".json", ".txt"), "w") as f:
            f.write(txt_transcript)
    except Exception:
        pass
