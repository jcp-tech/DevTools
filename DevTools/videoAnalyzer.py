# VISION/tools/videoAnalyzer.py #### need for the taking how we convert a Agent as Tool
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any, Optional, List
import os
import tempfile
import base64
from pathlib import Path

# Google Cloud imports
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import mimetypes

# Import existing YouTube downloader

"""
Video Analyzer Tool for ADK Agent
Analyzes video content (transcript + visuals) from MP4 files or YouTube URLs.
Uses Google Vertex AI for Speech-to-Text and Gemini for visual analysis.
"""

# Get the repository root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _extract_audio_transcript(video_path: str, language_code: str = "en-US") -> tuple[bool, str, str]:
    """
    Extract audio transcript from video using Google Speech-to-Text.
    
    Args:
        video_path: Path to the video file
        language_code: Language code for transcription (default: en-US)
        
    Returns:
        tuple: (success: bool, transcript: str, error: str)
    """
    try:
        # For now, we'll use Gemini's video understanding which includes audio
        # This is more efficient than separate STT
        return True, "", None
    except Exception as e:
        return False, None, str(e)


def _analyze_video_with_gemini(
    video_path: str,
    analysis_prompt: str = None
) -> tuple[bool, Dict[str, Any], str]:
    """
    Analyze video content using Gemini multimodal model.
    
    Args:
        video_path: Path to the video file
        analysis_prompt: Custom prompt for analysis
        
    Returns:
        tuple: (success: bool, analysis_result: dict, error: str)
    """
    try:
        # Initialize Vertex AI
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        if not project_id:
            return False, None, "GOOGLE_CLOUD_PROJECT environment variable not set"
        
        vertexai.init(project=project_id, location=location)
        
        # Use Gemini 2.0 Flash for video understanding
        model = GenerativeModel("gemini-2.0-flash-exp")
        
        # Read video file
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Create video part
        video_part = Part.from_data(
            data=video_data,
            mime_type="video/mp4"
        )
        
        # Default analysis prompt if none provided
        if not analysis_prompt:
            analysis_prompt = """Analyze this video comprehensively and provide:

1. TRANSCRIPT: Full transcript of all spoken words and audio content
2. VISUAL SUMMARY: Describe the key visual elements, scenes, and actions
3. KEY MOMENTS: Identify important timestamps and what happens at each
4. TOPICS: Main topics and themes discussed or shown
5. PEOPLE: Describe any people visible (appearance, actions, roles)
6. TEXT: Any visible text, captions, or written content
7. OBJECTS: Important objects, products, or items shown
8. SETTING: Environment, location, and context
9. MOOD/TONE: Overall atmosphere and emotional tone
10. INSIGHTS: Key takeaways, insights, or conclusions

Provide detailed, structured output."""
        
        # Generate content
        response = model.generate_content([video_part, analysis_prompt])
        
        # Parse response
        analysis_result = {
            "full_analysis": response.text,
            "model_used": "gemini-2.0-flash-exp",
            "prompt": analysis_prompt
        }
        
        return True, analysis_result, None
        
    except Exception as e:
        return False, None, str(e)


def analyze_video(
    source: str,
    source_type: str = "auto",
    analysis_type: str = "full",
    custom_prompt: Optional[str] = None,
    language_code: str = "en-US",
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Analyze video content including transcript and visuals.

    Args:
        source: Either a YouTube URL or path to local MP4 file
        source_type: Type of source - "youtube", "file", or "auto" (default: "auto")
        analysis_type: Type of analysis - "full", "transcript", or "visual" (default: "full")
        custom_prompt: Custom analysis prompt for specific needs
        language_code: Language code for transcription (default: "en-US")
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with video analysis results including transcript and visual analysis
    """
    temp_video_path = None
    cleanup_file = False
    
    try:
        # Determine source type
        if source_type == "auto":
            if source.startswith("http://") or source.startswith("https://") or "youtube.com" in source or "youtu.be" in source:
                source_type = "youtube"
            else:
                source_type = "file"
        
        # Get video file
        if source_type == "youtube":
            print(f"Downloading video from YouTube: {source}")
            
            # Create temp directory for download
            temp_dir = tempfile.mkdtemp()
            success, video_path, error = _download_video_internal(source, temp_dir)
            
            if not success:
                return {
                    "success": False,
                    "error": f"Failed to download video: {error}",
                    "source": source,
                    "source_type": "youtube"
                }
            
            temp_video_path = video_path
            cleanup_file = True
            
        else:  # file
            # Handle relative paths from repo root
            if not os.path.isabs(source):
                video_path = os.path.join(REPO_ROOT, source)
            else:
                video_path = source
            
            if not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": f"Video file not found: {source}",
                    "source": source,
                    "source_type": "file"
                }
            
            temp_video_path = video_path
            cleanup_file = False
        
        # Get video file info
        video_size = os.path.getsize(temp_video_path)
        video_size_mb = video_size / (1024 * 1024)
        
        print(f"Analyzing video: {temp_video_path} ({video_size_mb:.2f} MB)")
        
        # Perform analysis based on type
        result = {
            "success": True,
            "source": source,
            "source_type": source_type,
            "video_size_mb": round(video_size_mb, 2),
            "analysis_type": analysis_type
        }
        
        if analysis_type in ["full", "visual", "transcript"]:
            # Use Gemini for comprehensive analysis (includes both transcript and visuals)
            print("Performing Gemini video analysis...")
            
            success, analysis, error = _analyze_video_with_gemini(
                temp_video_path,
                custom_prompt
            )
            
            if not success:
                return {
                    "success": False,
                    "error": f"Video analysis failed: {error}",
                    "source": source,
                    "source_type": source_type
                }
            
            result["analysis"] = analysis
            result["message"] = "Video analysis completed successfully"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error analyzing video: {str(e)}",
            "source": source
        }
    
    finally:
        # Cleanup temporary files if needed
        if cleanup_file and temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                # Also remove temp directory if empty
                temp_dir = os.path.dirname(temp_video_path)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                print(f"Warning: Could not cleanup temp file: {e}")


def analyze_video_transcript_only(
    source: str,
    source_type: str = "auto",
    language_code: str = "en-US",
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Extract and analyze only the transcript from a video.

    Args:
        source: Either a YouTube URL or path to local MP4 file
        source_type: Type of source - "youtube", "file", or "auto" (default: "auto")
        language_code: Language code for transcription (default: "en-US")
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with transcript and audio analysis
    """
    custom_prompt = """Transcribe all spoken words in this video. Provide:

1. FULL TRANSCRIPT: Complete word-for-word transcription with timestamps
2. SPEAKERS: Identify different speakers if multiple people speak
3. KEY TOPICS: Main topics discussed
4. SUMMARY: Brief summary of what was said

Format the transcript clearly with timestamps."""
    
    return analyze_video(
        source=source,
        source_type=source_type,
        analysis_type="transcript",
        custom_prompt=custom_prompt,
        language_code=language_code,
        tool_context=tool_context
    )


def analyze_video_visuals_only(
    source: str,
    source_type: str = "auto",
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Analyze only the visual content of a video (no audio/transcript).

    Args:
        source: Either a YouTube URL or path to local MP4 file
        source_type: Type of source - "youtube", "file", or "auto" (default: "auto")
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with visual analysis results
    """
    custom_prompt = """Analyze the visual content of this video. Provide:

1. SCENE BREAKDOWN: Describe each major scene or segment
2. VISUAL ELEMENTS: Key visual elements, objects, people, settings
3. ACTIONS: What actions and events occur
4. TEXT ON SCREEN: Any text, captions, or graphics shown
5. VISUAL STYLE: Cinematography, editing style, visual quality
6. KEY FRAMES: Describe important moments or frames
7. OVERALL NARRATIVE: Visual story being told

Focus only on what can be seen, not audio content."""
    
    return analyze_video(
        source=source,
        source_type=source_type,
        analysis_type="visual",
        custom_prompt=custom_prompt,
        tool_context=tool_context
    )


def analyze_video_with_custom_prompt(
    source: str,
    analysis_prompt: str,
    source_type: str = "auto",
    analysis_type: str = "full",
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Analyze video with a custom analysis prompt for specific needs.

    Args:
        source: Either a YouTube URL or path to local MP4 file
        analysis_prompt: Custom prompt describing what to analyze
        source_type: Type of source - "youtube", "file", or "auto" (default: "auto")
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with custom analysis results
    """
    return analyze_video(
        source=source,
        source_type=source_type,
        analysis_type=analysis_type,
        custom_prompt=analysis_prompt,
        tool_context=tool_context
    )


