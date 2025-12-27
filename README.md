# Whisper ASR Video Transcription

Local GPU-accelerated video transcription using OpenAI Whisper.

## Quick Start

1. **Setup secrets** (only if using WhisperX diarization)
   ```bash
   cp secrets.env.example secrets.env
   # Edit secrets.env and add your HuggingFace token
   ```

2. **Start the service**
   ```bash
   docker compose up -d
   # if using secrets.env
   docker compose --env-file secerts.env up -d
   ```

3. **Add videos to transcribe**
   ```bash
   cp your_video.mp4 data/videos/
   ```

4. **Run transcription**
   ```bash
   python transcribe_videos.py
   ```

5. **Check results**
   ```bash
   ls data/transcribed/
   ```

## Configuration

### Service Settings (in `docker-compose.yml`)

**Engine:**
- `openai_whisper`: Most accurate, slower
- `faster_whisper`: 4-5x faster, recommended
- `whisperx`: Adds speaker diarization (requires HF_TOKEN)

**Model:**
- `tiny`, `base`: Fast but less accurate
- `small`, `medium`: Balanced
- `large-v3`, `turbo`: Most accurate, slower

### Transcription Settings (in `transcribe_videos.py`)

- `OUTPUT_FORMAT`: `json`, `text`, `srt`, `vtt`, `tsv`
- `TASK`: `transcribe` (original language) or `translate` (to English)
- `LANGUAGE`: Auto-detect or specify (e.g., `"en"`, `"es"`, `"fr"`)
- `WORD_TIMESTAMPS`: Word-level timing (faster_whisper/whisperx)
- `DIARIZE`: Speaker identification (whisperx + HF_TOKEN required)

## Supported Formats

**Video**: mp4, mkv, avi, mov, webm, flv, wmv  
**Audio**: mp3, wav, flac, aac, ogg, m4a, opus

All formats auto-converted via FFmpeg.

## API Access

Interactive docs: http://localhost:9000/docs

### Example cURL

```bash
curl -X POST "http://localhost:9000/asr?output=json" \
  -F "audio_file=@data/videos/sample.mp4"
```

## Requirements

- Docker with NVIDIA GPU support (or use CPU mode)
- Python 3.7+ with `requests` library
- HuggingFace token (only for WhisperX speaker diarization)

## Troubleshooting

**Service not starting?**
- Check GPU: `nvidia-smi`
- View logs: `docker compose logs -f`

**"Connection refused" error?**
- Ensure service is running: `docker compose ps`
- Wait for model download on first run

**Python import error?**
```bash
pip install requests
```
