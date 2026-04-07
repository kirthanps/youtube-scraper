# Translate_Subtitles.ipynb

## What this notebook does
- Batch-translates timestamped English subtitle lines into multiple Indian languages.
- Uses NLLB-200 model for neural machine translation.
- Preserves original timestamps while replacing text content.

## Inputs and outputs
- Inputs:
  - `to_translate.zip` / extracted JSON queue.
  - `transcription_english` arrays from each JSON.
  - Hugging Face translation model and tokenizer.
- Outputs:
  - Updated JSON files with language-specific `transcription_<lang>` keys.

## Main workflow
1. Install dependencies and load translation model.
2. Read queue files to process.
3. For each subtitle line, split `[timestamp] text` into parts.
4. Batch-translate text section per target language.
5. Reattach original timestamp and save translated lines.
6. Write updated JSON files.

## Visual: per-line transformation
```mermaid
flowchart LR
    A[[12:03.200] Add oil and cumin] --> B[Split timestamp + text]
    B --> C[Translate text in batch]
    C --> D[[12:03.200] translated sentence]
```

## Notes and risks
- Notebook is typically tuned for GPU-enabled environments.
- Timestamp parser assumes stable bracketed format.
- Translation quality varies by domain and language pair.
