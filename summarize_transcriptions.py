"""
Batch summarize and organize meeting transcriptions using Ollama.
Handles long documents by chunking and recursive summarization.
"""

import os
import json
from pathlib import Path
from datetime import datetime
import requests


class TranscriptionSummarizer:
    def __init__(self, model_name="gpt-oss:120b", ollama_url="http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.chunk_size = 6000  # Characters per chunk (adjust based on model's context window)
        self.overlap = 500  # Overlap between chunks to maintain context
        
    def get_model_info(self):
        """Check if model is available and get its context window."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/show",
                json={"name": self.model_name}
            )
            if response.status_code == 200:
                info = response.json()
                print(f"✓ Model {self.model_name} is available")
                return info
            else:
                print(f"⚠ Warning: Could not get model info (status {response.status_code})")
                return None
        except Exception as e:
            print(f"⚠ Warning: Could not connect to Ollama: {e}")
            return None
    
    def chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 200 chars
                chunk_end = text[max(start, end-200):end]
                sentence_ends = ['.', '!', '?', '\n\n']
                last_break = -1
                
                for ending in sentence_ends:
                    pos = chunk_end.rfind(ending)
                    if pos > last_break:
                        last_break = pos
                
                if last_break > 0:
                    end = max(start, end-200) + last_break + 1
            
            chunks.append(text[start:end].strip())
            start = end - self.overlap
            
        return chunks
    
    def call_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Call Ollama API with the given prompt."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=300  # 5 minute timeout
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                print(f"Error: Ollama API returned status {response.status_code}")
                return None
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return None
    
    def summarize_chunk(self, chunk: str, is_partial: bool = False) -> str:
        """Summarize a single chunk of text."""
        if is_partial:
            prompt = f"""Summarize this portion of a meeting transcript. Focus on key points, decisions, and action items:

{chunk}

Provide a concise summary covering main topics discussed."""
        else:
            prompt = f"""Summarize this meeting transcript. Focus on:
- Key topics discussed
- Decisions made
- Action items
- Important insights or concerns

Transcript:
{chunk}

Provide a well-organized summary."""
        
        return self.call_ollama(prompt)
    
    def combine_summaries(self, summaries: list[str]) -> str:
        """Combine multiple chunk summaries into a final summary."""
        combined = "\n\n---\n\n".join(summaries)
        
        prompt = f"""The following are summaries of different parts of the same meeting transcript. 
Combine them into a single, coherent summary that:
- Eliminates redundancy
- Organizes information logically
- Highlights key decisions and action items
- Maintains chronological flow where relevant

Partial summaries:
{combined}

Provide the final combined summary."""
        
        return self.call_ollama(prompt)
    
    def extract_metadata(self, filename: str, content: str) -> dict:
        """Extract metadata from filename and content."""
        # Parse filename: 2024-10-14_11-01-16 -- [HT] 1st meeting w dr rapp.txt
        parts = filename.replace('.txt', '').split(' -- ', 1)
        
        metadata = {
            "filename": filename,
            "date": parts[0] if parts else "unknown",
            "title": parts[1] if len(parts) > 1 else filename,
            "word_count": len(content.split()),
            "char_count": len(content)
        }
        
        return metadata
    
    def organize_summary(self, summary: str, metadata: dict) -> dict:
        """Create organized output structure."""
        # Ask Ollama to extract structured information
        prompt = f"""From this meeting summary, extract:
1. Meeting Title/Subject
2. Date (if mentioned in content): {metadata['date']}
3. Participants (list names if mentioned)
4. Key Topics (list main discussion points)
5. Decisions Made (list any decisions)
6. Action Items (list any tasks or follow-ups)
7. Tags (3-5 relevant keywords)

Meeting Summary:
{summary}

Respond in JSON format with these fields: title, date, participants, topics, decisions, action_items, tags"""
        
        response = self.call_ollama(prompt)
        
        # Try to parse JSON, fallback to simple structure
        try:
            structured = json.loads(response)
        except:
            structured = {
                "title": metadata["title"],
                "date": metadata["date"],
                "raw_summary": summary
            }
        
        structured["metadata"] = metadata
        structured["summary"] = summary
        
        return structured
    
    def process_file(self, filepath: Path) -> dict:
        """Process a single transcription file."""
        print(f"\n📄 Processing: {filepath.name}")
        
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata
        metadata = self.extract_metadata(filepath.name, content)
        print(f"   Length: {metadata['word_count']:,} words, {metadata['char_count']:,} characters")
        
        # Chunk if necessary
        chunks = self.chunk_text(content)
        print(f"   Split into {len(chunks)} chunk(s)")
        
        # Summarize chunks
        if len(chunks) == 1:
            print(f"   Summarizing...")
            summary = self.summarize_chunk(chunks[0], is_partial=False)
        else:
            chunk_summaries = []
            for i, chunk in enumerate(chunks, 1):
                print(f"   Summarizing chunk {i}/{len(chunks)}...")
                chunk_summary = self.summarize_chunk(chunk, is_partial=True)
                if chunk_summary:
                    chunk_summaries.append(chunk_summary)
            
            print(f"   Combining {len(chunk_summaries)} summaries...")
            summary = self.combine_summaries(chunk_summaries)
        
        if not summary:
            print(f"   ❌ Failed to generate summary")
            return None
        
        # Organize
        print(f"   Organizing summary...")
        organized = self.organize_summary(summary, metadata)
        
        print(f"   ✅ Complete")
        return organized
    
    def process_directory(self, input_dir: str, output_dir: str):
        """Process all transcription files in a directory."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get all .txt files
        txt_files = sorted(input_path.glob("*.txt"))
        
        if not txt_files:
            print(f"No .txt files found in {input_dir}")
            return
        
        print(f"\n{'='*60}")
        print(f"Found {len(txt_files)} transcription files")
        print(f"{'='*60}")
        
        # Check model
        self.get_model_info()
        
        # Process each file
        results = []
        failed = []
        
        for i, filepath in enumerate(txt_files, 1):
            print(f"\n[{i}/{len(txt_files)}]", end=" ")
            
            try:
                result = self.process_file(filepath)
                if result:
                    results.append(result)
                    
                    # Save individual summary
                    output_file = output_path / f"{filepath.stem}_summary.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                else:
                    failed.append(filepath.name)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed.append(filepath.name)
        
        # Save combined index
        print(f"\n{'='*60}")
        print(f"Saving combined index...")
        index_file = output_path / "all_summaries_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                "processed_date": datetime.now().isoformat(),
                "total_files": len(txt_files),
                "successful": len(results),
                "failed": len(failed),
                "failed_files": failed,
                "summaries": results
            }, f, indent=2, ensure_ascii=False)
        
        # Create readable markdown summary
        md_file = output_path / "all_summaries.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Meeting Transcription Summaries\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total files processed: {len(results)}/{len(txt_files)}\n\n")
            f.write(f"---\n\n")
            
            for result in results:
                f.write(f"## {result.get('title', 'Untitled')}\n\n")
                f.write(f"**Date:** {result.get('date', 'Unknown')}\n\n")
                
                if 'participants' in result and result['participants']:
                    f.write(f"**Participants:** {', '.join(result['participants'])}\n\n")
                
                f.write(f"### Summary\n\n{result['summary']}\n\n")
                
                if 'topics' in result and result['topics']:
                    f.write(f"**Topics:** {', '.join(result['topics'])}\n\n")
                
                if 'decisions' in result and result['decisions']:
                    f.write(f"**Decisions:**\n")
                    for decision in result['decisions']:
                        f.write(f"- {decision}\n")
                    f.write(f"\n")
                
                if 'action_items' in result and result['action_items']:
                    f.write(f"**Action Items:**\n")
                    for item in result['action_items']:
                        f.write(f"- {item}\n")
                    f.write(f"\n")
                
                f.write(f"---\n\n")
        
        print(f"✅ Processing complete!")
        print(f"   Successful: {len(results)}")
        print(f"   Failed: {len(failed)}")
        print(f"\nOutput saved to: {output_path}")
        print(f"   - Individual summaries: *_summary.json")
        print(f"   - Combined index: all_summaries_index.json")
        print(f"   - Readable format: all_summaries.md")


def main():
    # Configuration
    INPUT_DIR = "/home/tkeskinoglu/whisper/data/transcribed"
    OUTPUT_DIR = "/home/tkeskinoglu/whisper/data/summaries"
    MODEL_NAME = "gpt-oss:120b"
    
    # Create summarizer
    summarizer = TranscriptionSummarizer(model_name=MODEL_NAME)
    
    # Process all transcriptions
    summarizer.process_directory(INPUT_DIR, OUTPUT_DIR)


if __name__ == "__main__":
    main()
