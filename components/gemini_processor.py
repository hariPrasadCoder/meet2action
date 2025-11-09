"""Process transcripts with Gemini LLM to extract action items."""
import json
import streamlit as st
from google import generativeai as genai
from utils.env_loader import get_gemini_api_key
from typing import List, Dict


def initialize_gemini():
    """Initialize Gemini API client."""
    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-pro')


def extract_action_items(transcript_text: str) -> List[Dict]:
    """
    Extract action items from transcript using Gemini LLM.
    
    Args:
        transcript_text: Cleaned transcript text
        
    Returns:
        List of action item dictionaries with keys: assignee, task, priority
    """
    if not transcript_text:
        return []
    
    try:
        model = initialize_gemini()
        
        prompt = f"""You are a meeting assistant. Analyze the following meeting transcript and extract all action items.

For each action item, identify:
1. The task/action to be completed
2. The assignee name (who is responsible)
3. The priority level (High, Medium, Low) if mentioned, otherwise default to Medium

Return the results as a JSON array with the following structure:
[
  {{"assignee": "Name", "task": "Task description", "priority": "High/Medium/Low"}},
  ...
]

If no action items are found, return an empty array [].

Transcript:
{transcript_text}

JSON Response:"""
        
        with st.spinner("Processing transcript with Gemini..."):
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Try to find JSON in the response (might have markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            action_items = json.loads(response_text)
            
            # Validate structure
            validated_items = []
            for item in action_items:
                if isinstance(item, dict) and "task" in item:
                    validated_items.append({
                        "assignee": item.get("assignee", "Unassigned"),
                        "task": item.get("task", ""),
                        "priority": item.get("priority", "Medium")
                    })
            
            return validated_items
            
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse Gemini response as JSON: {str(e)}")
        if 'response_text' in locals():
            st.code(response_text)
        return []
    except Exception as e:
        st.error(f"Error processing transcript with Gemini: {str(e)}")
        return []


def process_transcript(transcript_text: str) -> List[Dict]:
    """
    Process transcript and return action items.
    Alias for extract_action_items for consistency.
    
    Args:
        transcript_text: Transcript text
        
    Returns:
        List of action item dictionaries
    """
    return extract_action_items(transcript_text)

