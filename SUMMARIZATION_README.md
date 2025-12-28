# Transcription Summarization Guide

## Overview
This solution automatically processes meeting transcriptions using a local Ollama GPT-OSS model. It handles long documents that exceed context windows through intelligent chunking and recursive summarization.

## How It Works

### 1. **Chunking Strategy**
- Long transcriptions are split into ~6000 character chunks (configurable)
- Chunks overlap by 500 characters to maintain context
- Smart boundary detection (breaks at sentences when possible)

### 2. **Recursive Summarization**
- Short files: Direct summarization
- Long files: 
  1. Each chunk summarized individually
  2. Chunk summaries combined into final summary
  3. Ensures entire content is processed

### 3. **Structured Organization**
- Extracts metadata (date, title, participants)
- Identifies key topics, decisions, action items
- Tags meetings for easy searching
- Outputs in both JSON and Markdown formats

## Usage

### Step 1: Test Ollama Connection
```bash
python test_ollama.py
```

This verifies:
- Ollama is running
- GPT-OSS model is available
- Model can respond to prompts

### Step 2: Run Batch Processing
```bash
python summarize_transcriptions.py
```

This will:
- Process all `.txt` files in `data/transcribed/`
- Create summaries in `data/summaries/`
- Generate three outputs:
  1. **Individual JSON files**: `*_summary.json` for each meeting
  2. **Combined index**: `all_summaries_index.json` with all data
  3. **Readable format**: `all_summaries.md` for easy browsing

### Progress Tracking
The script shows real-time progress:
```
[1/53] 📄 Processing: 2024-10-14_11-01-16 -- 1st meeting.txt
   Length: 15,234 words, 89,456 characters
   Split into 15 chunk(s)
   Summarizing chunk 1/15...
   Summarizing chunk 2/15...
   ...
   Combining 15 summaries...
   Organizing summary...
   ✅ Complete
```

## Configuration

Edit `summarize_transcriptions.py` to adjust:

```python
# In __init__:
self.chunk_size = 6000      # Characters per chunk
self.overlap = 500          # Overlap between chunks

# In main():
MODEL_NAME = "gpt-oss:120b" # Change model if needed
```

### Adjusting Chunk Size
- **Smaller chunks** (3000-4000): Faster, more granular, but may lose broader context
- **Larger chunks** (8000-10000): Better context, but may exceed model limits
- **Context window unknown?** Start with 6000 and adjust based on errors

## Output Structure

### Individual Summary JSON
```json
{
  "title": "1st meeting",
  "date": "2024-10-14_11-01-16",
  "participants": ["Dr. Herald", "..."],
  "topics": ["Topic 1", "Topic 2"],
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": ["Task 1", "Task 2"],
  "tags": ["healthcare", "partnership", "initial"],
  "summary": "Full narrative summary...",
  "metadata": {
    "filename": "...",
    "word_count": 15234,
    "char_count": 89456
  }
}
```

### Markdown Output
Easy-to-read format with all meetings organized chronologically, searchable in any text editor.

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Check if Ollama is running
ollama list

# Start Ollama if needed
ollama serve
```

### "Model not found"
```bash
# Check available models
ollama list

# Pull GPT-OSS if needed (adjust model name)
ollama pull gpt-oss:120b
```

### Processing Too Slow
- Reduce chunk size for faster processing
- Process subset first: modify `INPUT_DIR` to a subfolder
- Consider using a smaller, faster model for initial pass

### Memory Issues
The script processes files sequentially to avoid memory problems. If you still have issues:
- Reduce `chunk_size`
- Ensure Ollama has sufficient RAM allocated
- Close other applications

## Estimated Processing Time

With GPT-OSS 120B model:
- Short transcription (5-10 min meeting): ~30-60 seconds
- Medium transcription (30 min meeting): ~2-4 minutes  
- Long transcription (60+ min meeting): ~5-10 minutes

## Tips

1. **Run overnight**: Start the process before bed for long batches
2. **Test first**: Process 2-3 files first to verify quality
3. **Iterative refinement**: Adjust prompts in the script if summaries need more detail
4. **Backup originals**: Original transcriptions are never modified

## Alternative: Smaller Model
If processing is too slow, consider using a faster model:

```python
MODEL_NAME = "devstral:24b"  # or "qwen3-coder:latest"
```

Smaller models are faster but may produce less detailed summaries.
