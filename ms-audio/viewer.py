import plotly.graph_objects as go
import os
from typing import Dict, List, Optional, Tuple
from .helper import MultiFileHandler, RTTMLine, Segment, TextObject, read_rttm, read_split, read_text
from pydub import AudioSegment
from plotly.subplots import make_subplots
from plotly.graph_objects import Scatter
import numpy as np
from colour import Color


def perc_c(v: float) -> str:
    color: str = list(Color("blue").range_to("red", 101))[int(v*100)].get_hex()
    return color


def pydub_to_np(audio: AudioSegment) -> Tuple[np.ndarray, np.ndarray]:
    """
    Converts pydub audio segment into np.float32 of shape [duration_in_seconds*sample_rate, channels],
    where each value is in range [-1.0, 1.0]. 
    Returns tuple (audio_np_array, sample_rate).
    """
    channels = audio.channels
    sample_width = audio.sample_width
    frame_rate = audio.frame_rate
    assert channels is not None
    assert frame_rate is not None
    assert sample_width is not None
    y = np.array(audio.get_array_of_samples(), dtype=np.float32).reshape((-1, channels)) / (
        1 << (8 * sample_width - 1))
    t_max = len(y) / frame_rate
    x = np.linspace(start=0, stop=t_max, num=len(y))
    return x, y


def plot_rect(x0: float, x1: float, y0: float, y1: float, fillcolor: str, showlegend: bool = True, name: str = "", legend: Optional[str] = None) -> Tuple[Scatter, Scatter]:
    x_pos = x0+(x1-x0)/2
    y_pos = (y1-y0)/2
    if legend is None:
        legend = name
    box = go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[y0, y0, y1, y1, y0],
        mode='lines',
        name=name,
        meta=[name],
        hovertemplate='%{meta[0]}<extra></extra>',
        legendgroup=legend,
        line=dict(color="black"),
        fill='toself',
        fillcolor=fillcolor,
        showlegend=showlegend
    )

    # add the text in the center of each rectangle
    # skip hoverinfo since the rectangle itself already has hoverinfo
    label = go.Scatter(
        x=[x_pos],
        y=[y_pos],
        mode='text',
        legendgroup=legend,
        text=[name],
        hoverinfo='skip',
        textposition="middle center",
        showlegend=False
    )
    return box, label


# create our callback function
def split_clicked(trace, points, selector):
    print(trace, points, selector)


class MultiViewer(MultiFileHandler):
    def __init__(self, data_path: str, verbose: bool = False):
        super().__init__(data_path, verbose, "raw_audio_voices",  "output/analysis", "html")

    def handler(self, input_file: str, output_file: str, file_idx: int) -> None:
        diarization_path = input_file.replace(
            "raw_audio_voices", "diarization").replace(".wav", ".rttm")
        text_path = input_file.replace(
            "raw_audio_voices", "text").replace(".wav", ".json")
        split_path = input_file.replace(
            "raw_audio_voices", "voice_splits").replace(".wav", ".json")
        diarization: Optional[List[RTTMLine]] = None
        text: Optional[TextObject] = None
        splits: Optional[Dict[str, List[Segment]]] = None
        rows = 1
        if os.path.isfile(diarization_path):
            _id, diarization = read_rttm(diarization_path)
            rows += 1
        if os.path.isfile(diarization_path):
            text = read_text(text_path)
            rows += 1
        if os.path.isfile(split_path):
            splits = read_split(split_path)
            rows += 1
        audio_file: AudioSegment = AudioSegment.from_wav(input_file)
        # speakers = []
        # for d in diarization:
        #     if d["speaker"] not in speakers:
        #         speakers.append(d["speaker"])
        # num_speakers = len(speakers)
        # num_diaries = len(diarization)
        # num_text_segments = len(text)
        # print(
        #     f"\n\n{input_file}\nNumber of diaries: {num_diaries} ({num_speakers} speakers). Number of text-segments: {num_text_segments}")

        row = 1
        fig = make_subplots(rows=rows, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.02)
        audio_x, audio_y = pydub_to_np(audio_file)
        audio_subsampling = 20
        for channel in range(len(audio_y[1])):
            fig.add_trace(go.Scatter(x=audio_x[1::audio_subsampling], y=audio_y[:, channel]
                          [1::audio_subsampling], name=f'Channel {channel+1}'), row=row, col=1)
        row += 1

        speakers = []
        if diarization is not None:
            for d in diarization:
                if d["speaker"] not in speakers:
                    speakers.append(d["speaker"])
            for diary in diarization:
                y0 = 0
                y1 = 1
                x0 = diary["start"]
                x1 = x0+diary["duration"]
                # fig.add_shape(type="rect",
                #               x0=x0, y0=y0, x1=x1, y1=y1, name=diary["speaker"],
                #               #   line=dict(
                #               #       color="RoyalBlue",
                #               #       width=2,
                #               #   ),
                #               fillcolor=perc_c(speakers.index(
                #                   diary["speaker"])/len(speakers)),
                #               row=row, col=1
                #               ).update_layout(yaxis_title="Diarization")
                box, label = plot_rect(x0=x0, y0=y0, x1=x1, y1=y1, name=diary["speaker"],
                                       fillcolor=perc_c(speakers.index(
                                           diary["speaker"])/len(speakers)))
                fig.add_trace(box, row=row, col=1)
                fig.add_trace(label, row=row, col=1)
            row += 1
        if text is not None:
            # fig.add_trace(go.Scatter(x=[2, 3, 4], y=[100, 110, 120], name="Text"),
            #               row=row, col=1).update_layout(yaxis_title="Text")
            for segment in text["segments"]:
                y0 = 0
                y1 = 1
                x0 = segment["start"]
                x1 = segment["end"]
                # fig.add_shape(type="rect",
                #               x0=x0, y0=y0, x1=x1, y1=y1, name=segment["text"],
                #               #   line=dict(
                #               #       color="RoyalBlue",
                #               #       width=2,
                #               #   ),
                #               fillcolor="RoyalBlue",
                #               row=row, col=1
                #               ).update_layout(yaxis_title="Text")
                box, label = plot_rect(x0=x0, y0=y0, x1=x1, y1=y1, name=segment["text"],
                                       fillcolor="RoyalBlue")
                fig.add_trace(box, row=row, col=1)
                fig.add_trace(label, row=row, col=1)
            row += 1
        if splits is not None:
            # fig.add_trace(go.Scatter(x=[3, 4, 5], y=[1000, 1100, 1200], name="Splits", xaxis=""),
            #               row=row, col=1).update_layout(yaxis_title="Splits", xaxis_title="Zeit [s]")
            for speaker in splits:
                for line in splits[speaker]:
                    y0 = 0
                    y1 = 1
                    x0 = line["start"]
                    x1 = line["end"]
                    # fig.add_shape(type="rect",
                    #               x0=x0, y0=y0, x1=x1, y1=y1, name=line["text"],
                    #               #   line=dict(
                    #               #       color="RoyalBlue",
                    #               #       width=2,
                    #               #   ),
                    #               fillcolor=perc_c(speakers.index(
                    #                   speaker)/len(speakers)),
                    #               row=row, col=1
                    #               ).update_layout(yaxis_title="Splits")
                    box, label = plot_rect(x0=x0, y0=y0, x1=x1, y1=y1, name=line["text"],
                                           fillcolor=perc_c(speakers.index(
                                               speaker)/len(speakers)), legend=speaker)
                    fig.add_trace(box, row=row, col=1)
                    fig.add_trace(label, row=row, col=1)
                    # box.on_click(split_clicked)
            row += 1
        fig.update_layout(height=1000, width=1900,
                          title_text=f"Datei {input_file}",
                          yaxis_title="Wert",
                          legend_title="Legende",)
        # fig.show()
        fig.write_html(output_file)
