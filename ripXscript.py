"""
Description: Export a Rip In Various File Formats
Category: File
Shortcut:
Level: Intermediate
Version: 1.23
Copyright:	(c) Hit'n'Mix Ltd 2019-2021
Author:		Martin Dawe
License: 	Feel free to create an editable copy of this RipScript and base
			your own creations on it. Email to ripscripts@hitnmix.com and
			we will consider featuring it on the RipScripts page at
			hitnmix.com/ripscripts/
"""

import os
import shutil
import json
import platform
from tkinter import filedialog
from tkinter import messagebox
from typing import List

from pathlib import Path


def all_audio_files(path: str) -> List[str]:
    filetypes = ['mp3', 'aac', 'ogg', 'flac', 'alac', 'wav', 'aiff']

    files: List[str] = []
    for filetype in filetypes:
        for file in Path(path).rglob('*.'+filetype):
            files.append(os.path.relpath(file.resolve(), path))

    return files


def ripscript():
    # rip = ripx.current_view.rip

    # if rip is None:
    # 	ripx.pop_up("Export requires a rip to be loaded")
    # 	return

    file_types = [FLAC16, FLAC32, MP3, OGG32, STEM, WAV16, WAV24, WAV32]
    file_type_exts = [".flac", ".flac", ".mp3",
                      ".ogg", ".stem.mp4", ".wav", ".wav", ".wav"]
    file_type_names = ["FLAC 16-bit (.flac)", "FLAC 32-bit (.flac)", "MP3 (.mp3)", "OGG 32-bit (.ogg)", "Stem (.stem.mp4)",
                       "WAV 16-bit (.wav)", "WAV 24-bit (.wav)", "WAV 32-bit (.wav)"]
    if platform.system() == "Darwin":  # Mac OS X:
        file_types += [MP4, MOV]
        file_type_exts += [".mp4", ".mov"]
        file_type_names += ["MPEG-4 Movie (.mp4)", "QuickTime Movie (.mov)"]
    sample_rates = [192000, 96000, 88200, 64000, 48000, 44100, 32000, 22050, 0]
    sample_rate_names = ["192 kHz", "96 kHz", "88.2 kHz", "64 kHz",
                         "48 kHz", "44.1 kHz", "32 kHz", "22.05 kHz", "Same As Source"]
    channel_options = [1, 2]
    channel_option_names = ["Mono", "Stereo"]

    # Create window
    window = ripx.add_tk_window(sticky='NSWE')
    pad_x = 8 * pixel_scale()
    pad_y = 6 * pixel_scale()

    # Load settings and set defaults
    settings = Settings()
    settings.add("folder_name", "")
    settings.add("file_type", file_type_names[2])  # Default WAV16
    settings.add("sample_rate", sample_rate_names[8])  # Default same as source
    settings.add("channels", channel_option_names[1])  # Default stereo
    settings.add("selection", "all")

    # Name & folder label frame
    file_frame = window.add_label_frame(text=" Folder ")
    file_frame.grid(column=0, row=0, padx=pad_x, pady=pad_y, sticky="we")


    # Folder display and selection button
    # if folder_name.get() == "":
    #     folder_name.set(os.path.dirname(rip.file_name))
    folder_entry = file_frame.add_entry(
        textvariable=folder_name, state="readonly", width=64)
    folder_entry.grid(column=0, row=1, padx=pad_x, pady=pad_y, sticky="we")
    folder_button = file_frame.add_button(text=" Select Folder ")
    folder_button.grid(column=1, row=1, padx=pad_x, pady=pad_y, sticky="we")

    def select_folder(event: Event):
        folder = filedialog.askdirectory(
            initialdir=folder_name.get(), title="Select Export Folder")
        if folder != "":
            folder_name.set(folder)
    folder_button.bind("<Button-1>", select_folder)

    # Format frame
    format_frame = window.add_label_frame(text=" File Format ")
    format_frame.grid(column=0, row=1, padx=pad_x, pady=pad_y, sticky="we")

    # File type combo
    file_type_combo = format_frame.add_combo_box(
        values=file_type_names, textvariable=file_type, state="readonly")
    file_type_combo.grid(column=0, row=0, padx=pad_x, pady=pad_y)

    def file_type_selected(event: Event):
        # Sample rate/channels valid options?
        # To prevent selected text that shouldn't apply to read-only combo
        file_type_combo.selection_clear()
        file_type_id = file_types[file_type_combo.current()]
        if file_type_id == RIP or file_type_id == MP3 or file_type_id == MIDI or file_type_id == MIDINOTES or file_type_id == STEM:
            to_state = 'disabled'
        else:
            to_state = 'readonly'
        sample_rate_combo.config(state=to_state)
        channels_combo.config(state=to_state)
        # Selection valid options?
        # if file_type_id == RIP or file_type_id == MP4 or file_type_id == MOV:
        #     selection_button_all.grid_remove()
        #     selection_button_selection.grid_remove()
        #     selection_button_loop.grid_remove()
        # else:
        #     selection_button_all.grid(column=0, row=0, padx=pad_x, pady=pad_y)
        #     selection_button_selection.grid(
        #         column=1, row=0, padx=pad_x, pady=pad_y)
        #     selection_button_loop.grid(column=2, row=0, padx=pad_x, pady=pad_y)
    file_type_combo.bind("<<ComboboxSelected>>", file_type_selected)

    # Sample rate combo
    sample_rate_combo = format_frame.add_combo_box(
        values=sample_rate_names, textvariable=sample_rate, state="readonly")
    sample_rate_combo.grid(column=1, row=0, padx=pad_x, pady=pad_y)

    def sample_rate_selected(event: Event):
        # To prevent selected text that shouldn't apply to read-only combo
        sample_rate_combo.selection_clear()
    sample_rate_combo.bind("<<ComboboxSelected>>", sample_rate_selected)

    # Channels combo
    channels_combo = format_frame.add_combo_box(
        values=channel_option_names, textvariable=channels, state="readonly")
    channels_combo.grid(column=2, row=0, padx=pad_x, pady=pad_y)

    def channels_selected(event: Event):
        # To prevent selected text that shouldn't apply to read-only combo
        channels_combo.selection_clear()
    channels_combo.bind("<<ComboboxSelected>>", channels_selected)

    # What To Export frame
    selection_frame = window.add_label_frame(text=" What To Export ")
    selection_frame.grid(column=0, row=2, padx=pad_x, pady=pad_y, sticky="we")

    # Instrumentname entry
    global instrument_name
    instrument_name = StringVar()
    instrument_name.set("Voice")
    instrument_name_entry = selection_frame.add_entry(
        textvariable=instrument_name, width=64)
    instrument_name_entry.grid(column=0, row=0, columnspan=2,
                               padx=pad_x, pady=pad_y, sticky="we")

    # Files To Export frame
    files_frame = window.add_label_frame(text=" Files To Create ")
    files_frame.grid(column=0, row=3, padx=pad_x, pady=pad_y, sticky="we")

    # Set disabled items
    file_type_selected(None)

    # Export button and functionality
    export_button = window.add_button(text=" Process ")
    export_button.grid(column=0, row=4, padx=pad_x, pady=pad_y, sticky=(E))
    exporting = False

    def export_rip(event: Event):
        nonlocal exporting

        if exporting:
            return
        exporting = True
        root_dir = os.path.abspath(folder_name.get())
        # output_dir = os.path.join(
        #     os.path.dirname(root_dir), "raw_audio_voices")
        # files = all_audio_files(root_dir)
        # ripx.pop_up(", ".join(files))
        # os.makedirs(os.path.dirname(root_dir))
        for rip in ripx.riplist.rips:
            # input_path = os.path.join(root_dir, file)
            # output_path = os.path.join(output_dir, file)
            output_path = os.path.join(root_dir, rip.file_name)
            # os.makedirs(os.path.dirname(output_path))
            # rip = ripx.riplist.new_rip(input_path)

            i_name = instrument_name.get()
            # Create a temporary RipCut to store the piano notes
            ripcut = rip.new_ripcut(i_name)
            # Create a NoteGroup by filtering all notes in the rip that match the instrument_name and then copy it to the temporary RipCut
            rip.notes.filter(add=instrument(i_name)).copy_to(ripcut)
            # Export the RipCut as a 16-bit wav
            ripcut.export(file=output_path, type=file_types[file_type_combo.current()], samplerate=sample_rates[sample_rate_combo.current(
            )], channels=channel_options[channels_combo.current()])
            # If no longer need the RipCut, can delete it
            ripcut.delete()
    # rip = ripx.current_view.rip
    # if rip is None:
    # 	ripx.pop_up("Export requires a rip to be loaded")
    # 	exporting = False
    # 	return

    # # Get chosen file type
    # file_type_id = file_types[file_type_combo.current()]

    # # Check selection choice valid
    # ## NB No selection currently for MP4 or MOV files
    # if selection.get() == "all" or file_type_id == MP4 or file_type_id == MOV:
    # 	selection_group = 0  # All
    # elif selection.get() == "selection":
    # 	if rip.selected_notes is None or rip.selected_notes.end < 0:
    # 		selection_group = 0
    # 	else:
    # 		selection_group = rip.selected_notes
    # elif selection.get() == "loop":
    # 	if rip.loop_time_range is None or rip.loop_time_range.end < 0 or rip.loop_time_range.end < rip.loop_time_range.start + 0.001:
    # 		ripx.pop_up("Please set the loop markers or make a different selection")
    # 		exporting = False
    # 		return
    # 	else:
    # 		selection_group = rip.loop_time_range

    # # Is file type valid for the current rip?
    # if file_type_id == MP4 or file_type_id == MOV:
    # 	if rip.video_file_name is None:
    # 		ripx.pop_up(
    # 			"This rip does not contain any video, please select an audio format")
    # 		exporting = False
    # 		return

    # # Sample rate/channels
    # if file_type_id != RIP and file_type_id != MIDI and file_type_id != MIDINOTES:
    # 	sample_rate = sample_rates[sample_rate_combo.current()]
    # 	if sample_rate == 0:
    # 		sample_rate = rip.source_sample_rate
    # 	if sample_rate == 0:
    # 		ripx.pop_up(
    # 			"The source sample rate is unavailable.\n\nPlease select a sample rate.")
    # 		sample_rate_combo.current(5)
    # 		exporting = False
    # 		return
    # else:
    # 	# MIDI & RIP don't use sample rates as not waveform based
    # 	sample_rate = 0

    # channels = channels_combo.current()

    # # Options
    # options = 0
    # if file_type_id != STEM and file_type_id != RIP and file_type_id != MP4 and file_type_id != MOV:
    # 	if separation.get() == "layers":
    # 		options |= EXPORT_OPTION_SEPARATE_LAYERS
    # 	elif separation.get() == "stems":
    # 		options |= EXPORT_OPTION_SEPARATE_STEMS

    # # Check whether file exists and whether to delete
    # if options & (EXPORT_OPTION_SEPARATE_LAYERS | EXPORT_OPTION_SEPARATE_STEMS):
    # 	# We need to save to a given folder
    # 	file_path = os.path.join(folder_name.get(), file_name.get())
    # 	if os.path.isdir(file_path):
    # 		if messagebox.askyesno("Warning", "A folder already exists with this name.\n\nWould you like to OVERWRITE the ENTIRE FOLDER INCLUDING CONTENTS?"):
    # 			try:
    # 				shutil.rmtree(file_path)
    # 			except:
    # 				messagebox.showerror(message="The folder could not be overwritten.")
    # 				exporting = False
    # 				return
    # 		else:
    # 			exporting = False
    # 			return
    # 	if os.path.isfile(file_path):
    # 		if messagebox.askyesno("Warning", "A file already exists with this name.\n\nWould you like to overwrite it?"):
    # 			try:
    # 				os.remove(file_path)
    # 			except:
    # 				messagebox.showerror(message="The file could not be overwritten.")
    # 				exporting = False
    # 				return
    # 		else:
    # 			exporting = False
    # 			return
    # else:
    # 	# We need to save to a given file
    # 	file_path = os.path.join(folder_name.get(), file_name.get(
    # 	) + file_type_exts[file_type_combo.current()])
    # 	if os.path.isdir(file_path):
    # 		ripx.pop_up(
    # 			"A folder with this name already exists.\n\nPlease check it and remove first if required.")
    # 		exporting = False
    # 		return
    # 	if os.path.isfile(file_path):
    # 		if messagebox.askyesno("Warning", "A file already exists with this name.\n\nWould you like to overwrite it?"):
    # 			try:
    # 				os.remove(file_path)
    # 			except:
    # 				messagebox.showerror(message="The file could not be overwritten.")
    # 				exporting = False
    # 				return
    # 		else:
    # 			exporting = False
    # 			return

    # # Save state
    # settings.save()
    # window.winfo_toplevel().destroy()

    # # Export
    # result = rip.export(
    # 	file=file_path,
    # 	type=file_type_id,
    # 	sample_rate=sample_rate,
    # 	channels=channel_options[channels],
    # 	selection=selection_group,
    # 	options=options)
    # exporting = False
    # if result != EXPORT_SUCCESS:
    # 	if result == EXPORT_FILE_EXISTS:
    # 		ripx.pop_up("File already exists.")
    # 	elif result == EXPORT_VIDEO_FORMAT_UNAVAILABLE:
    # 		ripx.pop_up(
    # 			"This video format is not available for the source video format.")
    # 	else:
    # 		ripx.pop_up("There was a problem exporting the rip.")
    # 	return

    def export_cancel(event: Event):
        window.winfo_toplevel().destroy()
        return "break"

    export_button.bind("<Button-1>", export_rip)
    # Also press Enter to Export
    window.winfo_toplevel().bind("<Key-Return>", export_rip)
    # Cancel window
    window.winfo_toplevel().bind("<Key-Escape>", export_cancel)
