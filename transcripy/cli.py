import argparse
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-extract-voice", default=False, action='store_true',
                        help="extract voice from raw_audio")

    parser.add_argument("--audio-to-text", default=False, action='store_true',
                        help="extract text from raw_audio_voices")
    parser.add_argument("--audio-to-voices",  default=False, action='store_true',
                        help="create diarization from raw_audio_voices")
    parser.add_argument("--preprocess",  default=False, action='store_true',
                        help="Additional space before splits for --slice")

    parser.add_argument("--map-speakers",  default=False, action='store_true',
                        help="Map speakers between files")

    parser.add_argument("--set-speakers",  default=False, action='store_true',
                        help="Set speakers for diarization")

    parser.add_argument("--text-to-splits", default=False, action='store_true',
                        help="Split voices (after --audio-2-text and --audio-2-voices)")

    parser.add_argument("--create-dataset", default=None, type=str,
                        help="Create dataset for voice-cloning")

    parser.add_argument("--slice", default=False, action='store_true',
                        help="Create slices of .wav files")
    parser.add_argument("--viewer",  default=False, action='store_true',
                        help="Open viewer GUI")
    parser.add_argument("--transcribe",  default=False, action='store_true',
                        help="Transcribe files to console")

    parser.add_argument("--model",  type=str, default=None,
                        help="Model for --audio-to-text (default: 'medium') and --audio-to-voices (default: 'pyannote/speaker-diarization') and --audio-extract-voice (default: 'spleeter:2stems')")
    parser.add_argument("--language",  type=str, default=None,
                        help="Force language for --audio-to-text")
    parser.add_argument("--pre",  type=float, default=0,
                        help="Additional space before splits for --slice")
    parser.add_argument("--post",  type=float, default=0.2,
                        help="Additional space after splits for --slice")
    parser.add_argument("--threshold",  type=float, default=0.2,
                        help="Threshold for --map-speakers")
    parser.add_argument("--voice-synthesis",  default=False, action='store_true',
                        help="Open voice-synthesis GUI")
    parser.add_argument("--data-path", type=str, default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),
                        help="the path of the data")
    parser.add_argument("--verbose", default=False, action='store_true',
                        help="whether to print out the progress and debug messages")
    parser.add_argument("--extract-all", default=False, action='store_true',
                        help="Extract all voices from audio (--audio-extract-voice)")

    args = parser.parse_args()
    data_path = args.data_path
    model = None
    verbose = args.verbose
    if args.audio_extract_voice:
        if model is None:
            model = "spleeter:2stems"
        from .audioPreprocessing import MultiVoiceExtractor
        MultiVoiceExtractor(data_path, verbose=verbose,
                            model=model, vocals_only=not args.extract_all).run()
    if args.audio_to_text:
        if model is None:
            model = "medium"
        from .audio2text import MultiTranscriber
        MultiTranscriber(data_path, verbose=verbose, model=model,
                         forceLanguage=args.language, english_only=args.language == "english").run()
    if args.audio_to_voices:
        if model is None:
            model = "pyannote/speaker-diarization"
        from .audio2voices import MultiDetector
        MultiDetector(data_path, verbose=verbose, model=model).run()

    if args.preprocess:
        from .audio2text import MultiTranscriber
        from .audio2voices import MultiDetector
        MultiTranscriber(data_path, verbose=verbose).run()
        MultiDetector(data_path, verbose=verbose).run()

    if args.set_speakers:
        from .setSpeakers import MultiSpeakerSetter
        MultiSpeakerSetter(data_path, verbose=verbose).run()

    if args.map_speakers:
        from .mapSpeakers import MultiSpeakerMapper
        c= MultiSpeakerMapper(data_path, verbose=verbose)
        c.run()
        c.process(args.threshold)

    if args.text_to_splits:
        from .text2splits import MultiVoiceSplitter
        MultiVoiceSplitter(data_path, verbose=verbose).run()

    if args.transcribe:
        from .text2splits import MultiVoiceSplitter
        MultiVoiceSplitter(data_path, verbose=verbose, transcribe=True).run()
    if args.viewer:
        from .viewer import MultiViewer
        MultiViewer(data_path, verbose=verbose).run()
    if args.slice:
        from .sliceAudio import MultiSlicer
        MultiSlicer(data_path, verbose=verbose, pre=args.pre *
                    1000, post=args.post*1000).run()
    if args.create_dataset is not None:
        from .createDataset import DatasetCreator
        c = DatasetCreator(data_path, args.create_dataset, verbose=verbose, pre=args.pre *
                    1000, post=args.post*1000)
        c.run()
        c.sample_statistics()
        c.process_samples()

    if args.voice_synthesis:
        from .synthesizer import run
        run()


if __name__ == "__main__":
    main()