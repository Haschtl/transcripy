import os
from typing import Dict, TypedDict
from .helper import MultiFileHandler, Segment, read_split, slugify
from pydub import AudioSegment
from pydub.utils import mediainfo
from mutagen import wave
from mutagen.id3._frames import TextFrame, Frame


class MediaInfoMin(TypedDict):
    index: str
    title: str
    artist: str
    filename: str
    album: str
    genre: str


class MediaInfo(MediaInfoMin):
    # must change
    duration_ts: str
    duration: str
    bit_rate: str
    size: str
    # removable
    codec_name: str
    codec_long_name: str
    codec_tag_string: str
    codec_tag: str
    # may overwrite
    sample_rate: str
    time_base: str
    channels: str
    bits_per_sample: str
    bits_per_raw_sample: str
    format_name: str
    format_long_name: str
    # unused
    sample_fmt: str
    max_bit_rate: str
    channel_layout: str
    id: str
    r_frame_rate: str
    avg_frame_rate: str
    start_pts: str
    start_time: str
    nb_frames: str
    nb_read_frames: str
    nb_read_packets: str
    nb_streams: str
    mb_programs: str
    probe_score: str
    DISPOSITION: Dict[str, str]


# def create_metadata(index:int, speaker:str, filename:str,start:int,end:int,segment:Segment, metadata:MediaInfo) -> MediaInfoMin:
#     return {
#         "index":str(index),
#         "author": speaker,
#         "filename": os.path.split(filename)[1],
#         "album": metadata["filename"],
#         "genre": str(start/1000),
#         "title":segment["text"]
#     }
def set_metadata(wav_filename: str, index: int, speaker: str, orig_filename: str, start: int, end: int, segment: Segment, metadata: MediaInfo) -> None:
    album_name = metadata["filename"][metadata["filename"].find(
        "raw_audio_voices")+17:].replace("\\", " ")
    artist = speaker
    # turn it into an mp3 object using the mutagen library
    mp3file = wave.WAVE(wav_filename)
    # set the album name
    mp3file['album'] = TextFrame(encoding=3, text=[album_name])
    mp3file.tags["ALBUM"] = Frame(encoding=3, text=album_name)
    # set the albumartist name
    mp3file['albumartist'] = TextFrame(encoding=3, text=[artist])
    mp3file.tags["ARTIST"] = Frame(encoding=3, text=artist)
    # set the track number with the proper format
    mp3file['tracknumber'] = TextFrame(encoding=3, text=str(index))
    mp3file['filename'] = TextFrame(
        encoding=3, text=os.path.split(orig_filename)[1])
    mp3file['genre'] = TextFrame(encoding=3, text=str(start/1000))
    mp3file['title'] = TextFrame(encoding=3, text=segment["text"])
    # save the changes that we've made
    mp3file.tags.save(wav_filename)
    mp3file.save()


class MultiSlicer(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False, pre: float = 200.0, post: float = 0.0) -> None:
        super().__init__(data_path, verbose, "voice_splits",
                         "output/slices", None, ["json"])
        self.extra_ms = pre
        self.earlier_ms = post

    def handler(self, input_file: str, output_dir: str, file_idx: int) -> None:
        out_format = "wav"
        audio_path = input_file.replace(".json", ".wav").replace(
            "voice_splits", "raw_audio_voices")
        splits = read_split(input_file)
        audio_file: AudioSegment = AudioSegment.from_wav(audio_path)
        metadata: MediaInfo = mediainfo(audio_path)
        for person in splits:
            out_dir = os.path.join(output_dir, person)
            os.makedirs(out_dir, exist_ok=True)
            for split in splits[person]:
                out_filename = os.path.join(
                    out_dir, slugify(split["text"])+"."+out_format)
                t1 = int(split["start"]*1000-self.earlier_ms)
                t2 = int(split["end"]*1000+self.extra_ms+self.earlier_ms)
                a: AudioSegment = audio_file[t1:t2]
                # new_meta = create_metadata(file_idx, person, out_filename, t1, t2, split, metadata)

                a.export(out_filename, format=out_format)
                set_metadata(out_filename, file_idx, person,
                             out_filename, t1, t2, split, metadata)
