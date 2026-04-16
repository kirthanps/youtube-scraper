# YouTube Scraper Pipeline

This repository contains an end-to-end pipeline to collect YouTube video data from selected channels, enrich it with subtitles/transcriptions, optionally translate content, classify video type with LLM workflows, and export results to Excel.

The pipeline is built around per-video JSON files and state markers in channel ID files.

## What This Project Does

1. Collects video IDs for fixed YouTube channels.
2. Fetches metadata for each video.
3. Downloads and parses subtitles into timestamped transcription arrays.
4. Identifies videos missing English transcripts and prepares translation queues.
5. Runs optional notebook-based translation and ingredient extraction.
6. Classifies each video as `food`, `news`, `other`, or `unpredictable`.
7. Generates validation reports and final Excel output.

## Repository Structure

- [code/](code/): Executable scripts and notebooks.
- [code doc/](code%20doc/): Matching markdown documentation for each code file.
- [data/](data/): Active dataset, queues, translated files, summaries, and outputs.
- [pipeline.md](pipeline.md): High-level pipeline explanation.
- [requirements.txt](requirements.txt): Python package dependencies.

## Active Channels

The scripts are hardcoded for:

- masterchefnambie
- delhifoodwalks
- northeastindiafood
- roohi_haflongbar
- main_bhi_bharat

## Core Data Model

Each channel folder in [data/](data/) contains:

- `video_ids_<N>.txt`: source ID list and processing state tracker.
- `<SL>. <title-first-6-words>.json`: one JSON per video.
- `errors_<N>.txt`: optional metadata error log.

Translation-related shared paths:

- [data/to_translate](data/to_translate)
- [data/to_translate.txt](data/to_translate.txt)
- [data/translated](data/translated)

Final export:

- [data/channel_metadata.xlsx](data/channel_metadata.xlsx)

## ID File State Markers

`video_ids_<N>.txt` lines evolve through states:

- raw `video_id`: not processed
- `video_id 1`: metadata completed
- `video_id 1 1`: transcription completed
- `video_id e`: metadata failed (error-logging variant)

Note: marker integrity is critical. Manual edits can break resume and validation behavior.

## Setup

## 1) Python environment

Use Python 3.10+ recommended.

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2) Required external tools

- yt-dlp available in PATH.
- Internet access for YouTube metadata and subtitle retrieval.

## 3) Optional notebook/LLM environment

For notebook stages you will typically need:

- Jupyter environment
- PyTorch + Transformers stack
- GPU runtime for translation and classification notebooks

## Pipeline Run Order (Practical)

Run from repository root unless you have custom orchestration.

1. Collect IDs
   - [code/collect_and_verify_video_ids.py](code/collect_and_verify_video_ids.py)

2. Metadata extraction (choose one)
   - [code/process_youtube_metadata.py](code/process_youtube_metadata.py)
   - [code/process_youtube_with_error_logging.py](code/process_youtube_with_error_logging.py)

3. Subtitle/transcription stage (choose one)
   - [code/process_youtube_transcriptions.py](code/process_youtube_transcriptions.py)
   - [code/stage2_transcription.py](code/stage2_transcription.py)

4. Missing-English discovery and translation queue
   - [code/check_missing_english_transcripts.py](code/check_missing_english_transcripts.py)
   - [code/collect_files_for_translation.py](code/collect_files_for_translation.py)

5. Translation notebook (optional)
   - [code/Translate_Subtitles.ipynb](code/Translate_Subtitles.ipynb)

6. Restore translated files (optional)
   - [code/restore_translated_files.py](code/restore_translated_files.py)

7. Ingredient extraction notebook (optional)
   - [code/ingredients extractor.ipynb](code/ingredients%20extractor.ipynb)

8. Classification analysis and split prep
   - [code/description_transcription_stats.py](code/description_transcription_stats.py)
   - [code/length_analysis_classification.py](code/length_analysis_classification.py)
   - [code/Category classification preprocessing.ipynb](code/Category%20classification%20preprocessing.ipynb)

9. Video-type classification notebook
   - [code/Classification video_type category LLM.ipynb](code/Classification%20video_type%20category%20LLM.ipynb)

10. Validation, stats, and export
    - [code/video_type_stats.py](code/video_type_stats.py)
    - [code/verify_youtube_stage2.py](code/verify_youtube_stage2.py)
    - [code/channel_wise_transcript_stats.py](code/channel_wise_transcript_stats.py)
    - [code/excel_generator.py](code/excel_generator.py)

## Script Notes and Behavior Details

## Metadata scripts

- [code/process_youtube_metadata.py](code/process_youtube_metadata.py)
  - Creates JSON skeleton with metadata and one transcription key based on audio language.
  - Rewrites ID file after each success for crash-resume behavior.

- [code/process_youtube_with_error_logging.py](code/process_youtube_with_error_logging.py)
  - Same core metadata flow plus persistent error marking/logging.
  - Writes `e` marker and channel error file.

## Transcription scripts

- [code/process_youtube_transcriptions.py](code/process_youtube_transcriptions.py)
  - Uses yt-dlp with JS runtime configuration.
  - Removes existing transcription keys, then repopulates from available subtitles.

- [code/stage2_transcription.py](code/stage2_transcription.py)
  - Functionally overlapping alternative implementation.

Important: these two scripts overlap heavily. Use one consistently in a run.

## Translation queue and restore

- [code/collect_files_for_translation.py](code/collect_files_for_translation.py)
  - Copies files with non-English transcripts and missing English into queue.
  - Overwrites [data/to_translate.txt](data/to_translate.txt) each run.

- [code/restore_translated_files.py](code/restore_translated_files.py)
  - Restores translated files by filename mapping from [data/translated](data/translated).

## Validation and reporting

- [code/verify_youtube_stage2.py](code/verify_youtube_stage2.py): state and schema consistency checks.
- [code/channel_wise_transcript_stats.py](code/channel_wise_transcript_stats.py): transcript availability coverage per channel.
- [code/video_type_stats.py](code/video_type_stats.py): classification coverage and distribution.
- [code/excel_generator.py](code/excel_generator.py): final workbook generation.

## Notebook Stages

Notebook files in [code/](code/) are interactive/manual steps and are not chained automatically by Python scripts:

- [code/Translate_Subtitles.ipynb](code/Translate_Subtitles.ipynb)
- [code/ingredients extractor.ipynb](code/ingredients%20extractor.ipynb)
- [code/Category classification preprocessing.ipynb](code/Category%20classification%20preprocessing.ipynb)
- [code/Classification video_type category LLM.ipynb](code/Classification%20video_type%20category%20LLM.ipynb)

## Known Operational Caveats

1. Marker-based progress tracking is simple but fragile if files are edited manually.
2. Transcription stage may produce multiple `transcription_*` keys for some videos.
3. [code/verify_youtube_stage2.py](code/verify_youtube_stage2.py) validates strict JSON structure and marker consistency.
4. Translation restore depends on intact [data/to_translate.txt](data/to_translate.txt) mapping.
5. Two transcription scripts overlap; behavior can diverge if both are used inconsistently.

## Quick Commands

Examples from repository root:

```bash
python code/collect_and_verify_video_ids.py
python code/process_youtube_with_error_logging.py
python code/process_youtube_transcriptions.py
python code/check_missing_english_transcripts.py
python code/collect_files_for_translation.py
python code/restore_translated_files.py
python code/video_type_stats.py
python code/verify_youtube_stage2.py
python code/excel_generator.py
```

## Documentation Map

Each code file has a paired markdown document in [code doc/](code%20doc/). Start with:

- [pipeline.md](pipeline.md)
- [code doc/process_youtube_metadata.md](code%20doc/process_youtube_metadata.md)
- [code doc/process_youtube_transcriptions.md](code%20doc/process_youtube_transcriptions.md)
- [code doc/Classification video_type category LLM.md](code%20doc/Classification%20video_type%20category%20LLM.md)

## Status of Existing Data

The current workspace already contains populated channel folders and artifacts under [data/](data/). The pipeline can be resumed from existing marker state if files are consistent.
