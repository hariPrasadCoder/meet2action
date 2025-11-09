"""Parse and clean Google Meet transcripts."""
import re
from typing import List, Dict


def parse_transcript(raw_text: str) -> List[Dict]:
    """
    Parse raw transcript text into structured conversation.
    
    Args:
        raw_text: Raw transcript text from Google Docs
        
    Returns:
        List of dictionaries with keys: speaker, text, timestamp
    """
    if not raw_text:
        return []
    
    # Remove common transcript artifacts
    lines = raw_text.split('\n')
    parsed = []
    
    # Pattern to match timestamps (e.g., "00:01:23" or "1:23")
    timestamp_pattern = re.compile(r'^\d{1,2}:\d{2}(:\d{2})?\s')
    
    # Pattern to match speaker names (usually followed by colon)
    speaker_pattern = re.compile(r'^([A-Z][a-zA-Z\s]+):\s*(.+)$')
    
    current_speaker = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # Check if line starts with timestamp
        if timestamp_pattern.match(line):
            line = timestamp_pattern.sub('', line).strip()
        
        # Check if line contains speaker name
        speaker_match = speaker_pattern.match(line)
        if speaker_match:
            # Save previous speaker's text
            if current_speaker and current_text:
                parsed.append({
                    "speaker": current_speaker,
                    "text": " ".join(current_text)
                })
            
            # Start new speaker
            current_speaker = speaker_match.group(1).strip()
            current_text = [speaker_match.group(2).strip()]
        else:
            # Continue current speaker's text
            if current_speaker:
                current_text.append(line)
            else:
                # No speaker identified, treat as continuation
                if parsed:
                    parsed[-1]["text"] += " " + line
                else:
                    # First line without speaker
                    parsed.append({
                        "speaker": "Unknown",
                        "text": line
                    })
    
    # Add last speaker's text
    if current_speaker and current_text:
        parsed.append({
            "speaker": current_speaker,
            "text": " ".join(current_text)
        })
    
    return parsed


def clean_transcript(raw_text: str) -> str:
    """
    Clean raw transcript text by removing timestamps and formatting.
    
    Args:
        raw_text: Raw transcript text
        
    Returns:
        Cleaned transcript text
    """
    if not raw_text:
        return ""
    
    # Remove timestamps
    text = re.sub(r'\d{1,2}:\d{2}(:\d{2})?\s', '', raw_text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page breaks and form feeds
    text = text.replace('\f', ' ')
    
    return text.strip()


def extract_speakers(parsed_transcript: List[Dict]) -> List[str]:
    """
    Extract unique speaker names from parsed transcript.
    
    Args:
        parsed_transcript: List of parsed conversation dictionaries
        
    Returns:
        List of unique speaker names
    """
    speakers = set()
    for entry in parsed_transcript:
        if entry.get("speaker"):
            speakers.add(entry["speaker"])
    return sorted(list(speakers))

