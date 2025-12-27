#!/usr/bin/env python3
"""
Video transcription script using Whisper ASR webservice.

Processes all video files in data/videos/ and saves transcriptions to data/transcribed/
Supports multiple output formats (text, json, srt, vtt) and optional speaker diarization.
"""

import requests
import json
from pathlib import Path
from typing import Literal

# Configuration
API_URL = "http://localhost:9000/asr"
VIDEOS_DIR = Path("data/videos")
OUTPUT_DIR = Path("data/transcribed")

# Transcription settings
OUTPUT_FORMAT: Literal["text", "json", "srt", "vtt", "tsv"] = "text"
TASK: Literal["transcribe", "translate"] = "transcribe"
LANGUAGE = None  # None for auto-detect, or use "en", "es", "fr", etc.
WORD_TIMESTAMPS = True  # Enable word-level timestamps (requires faster_whisper)
VAD_FILTER = False  # Voice activity detection filtering (faster_whisper only)
DIARIZE = True  # Speaker diarization (whisperx only, requires HF_TOKEN)
MIN_SPEAKERS = 1  # Minimum speakers for diarization
MAX_SPEAKERS = 10  # Maximum speakers for diarization

# Supported video/audio extensions (via FFmpeg)
SUPPORTED_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv',  # Video
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.opus'  # Audio
}


def transcribe_file(video_path: Path) -> dict:
    """
    Transcribe a single video/audio file.
    
    Args:
        video_path: Path to the video/audio file
        
    Returns:
        dict: API response containing transcription
        
    Raises:
        requests.RequestException: If API request fails
    """
    # Build query parameters
    params = {
        "output": OUTPUT_FORMAT,
        "task": TASK,
        "word_timestamps": str(WORD_TIMESTAMPS).lower(),
        "vad_filter": str(VAD_FILTER).lower(),
        "encode": "true",  # Let FFmpeg handle encoding
    }
    
    if LANGUAGE:
        params["language"] = LANGUAGE
        
    if DIARIZE:
        params["diarize"] = "true"
        if MIN_SPEAKERS:
            params["min_speakers"] = MIN_SPEAKERS
        if MAX_SPEAKERS:
            params["max_speakers"] = MAX_SPEAKERS
    
    # Open file and send request
    with open(video_path, "rb") as f:
        files = {"audio_file": (video_path.name, f)}
        print(f"Transcribing: {video_path.name}...")
        response = requests.post(API_URL, params=params, files=files)
        response.raise_for_status()
    
    return response.json() if OUTPUT_FORMAT == "json" else {"text": response.text}


def save_transcription(video_path: Path, result: dict):
    """
    Save transcription result to file.
    
    Args:
        video_path: Original video file path
        result: Transcription result from API
    """
    # Create output filename based on format
    output_name = video_path.stem
    
    if OUTPUT_FORMAT == "json":
        output_path = OUTPUT_DIR / f"{output_name}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
    elif OUTPUT_FORMAT == "text":
        output_path = OUTPUT_DIR / f"{output_name}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.get("text", ""))
            
    elif OUTPUT_FORMAT in ["srt", "vtt", "tsv"]:
        output_path = OUTPUT_DIR / f"{output_name}.{OUTPUT_FORMAT}"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.get("text", ""))
    
    print(f"✓ Saved to: {output_path}")
    
    # Also save a summary for JSON output
    if OUTPUT_FORMAT == "json" and "text" in result:
        summary_path = OUTPUT_DIR / f"{output_name}_summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"✓ Summary saved to: {summary_path}")


def main():
    """Process all videos in the videos directory."""
    # Ensure directories exist
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all video files
    video_files = [
        f for f in VIDEOS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    
    if not video_files:
        print(f"No video files found in {VIDEOS_DIR}")
        print(f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        return
    
    print(f"Found {len(video_files)} file(s) to transcribe")
    print(f"Output format: {OUTPUT_FORMAT}")
    print(f"Task: {TASK}")
    print(f"Language: {LANGUAGE or 'auto-detect'}")
    print("-" * 50)
    
    # Process each file
    success_count = 0
    for video_path in video_files:
        try:
            result = transcribe_file(video_path)
            save_transcription(video_path, result)
            success_count += 1
            print()
        except requests.RequestException as e:
            print(f"✗ Error transcribing {video_path.name}: {e}")
            print()
        except Exception as e:
            print(f"✗ Unexpected error with {video_path.name}: {e}")
            print()
    
    print("-" * 50)
    print(f"Completed: {success_count}/{len(video_files)} files transcribed successfully")


if __name__ == "__main__":
    main()
