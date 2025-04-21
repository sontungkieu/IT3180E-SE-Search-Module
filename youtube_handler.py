import yt_dlp
import json
import os
import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

# Load a pre-trained embedding model once
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def get_youtube_transcript(url: str) -> tuple[List[list[Any]], str | None]:
    ydl_opts = {
        "quiet": True,
        "writesubtitles": True,
        "subtitleslangs": ["vi", "en"],
        "skip_download": True,
        "extractor_args": {
            "youtube": {"player_client": ["web"]}
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            subtitles = info_dict.get("subtitles", {})
            automatic_captions = info_dict.get("automatic_captions", {})

            subtitle_url = None
            selected_lang = None

            if "vi" in subtitles:
                subtitle_url = subtitles["vi"][0]["url"]
                selected_lang = "vi"
            elif "en" in subtitles:
                subtitle_url = subtitles["en"][0]["url"]
                selected_lang = "en"
            elif "vi" in automatic_captions:
                subtitle_url = automatic_captions["vi"][0]["url"]
                selected_lang = "vi (auto)"
            elif "en" in automatic_captions:
                subtitle_url = automatic_captions["en"][0]["url"]
                selected_lang = "en (auto)"
            elif subtitles:
                first_lang = next(iter(subtitles))
                subtitle_url = subtitles[first_lang][0]["url"]
                selected_lang = f"{first_lang} (manual)"
            elif automatic_captions:
                first_lang = next(iter(automatic_captions))
                subtitle_url = automatic_captions[first_lang][0]["url"]
                selected_lang = f"{first_lang} (auto)"
            else:
                print("No subtitles found.")
                return None, None

            transcript = ydl.urlopen(subtitle_url).read().decode("utf-8")
            transcript_dict = json.loads(transcript)
            return extract_utf_from_events(transcript_dict), selected_lang

        except Exception as e:
            print(f"Error occurred while fetching subtitles: {e}")
            return None, None

def extract_utf_from_events(data: dict) -> List[list[Any]]:
    utf_scripts = []

    for event in data["events"]:
        if "segs" in event:
            utf_event = []
            for seg in event["segs"]:
                if "utf8" in seg and seg["utf8"] != "\n":
                    utf_event.append(seg["utf8"])
            if utf_event:
                utf_scripts.append([event["tStartMs"], " ".join(utf_event)])

    return utf_scripts

def chunk_text(data: List[list[Any]], chunk_size: int = 250) -> List[Dict[str, Any]]:
    chunks = []
    current_chunk = []
    current_chunk_word_count = 0
    current_start_time = None

    for start_time, text in data:
        words = text.split()
        for word in words:
            if current_chunk_word_count >= chunk_size:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "timestamp": time_output(current_start_time)
                })
                current_chunk = []
                current_chunk_word_count = 0
                current_start_time = None

            if current_start_time is None:
                current_start_time = start_time

            current_chunk.append(word)
            current_chunk_word_count += 1

    if current_chunk:
        chunks.append({
            "text": " ".join(current_chunk),
            "timestamp": time_output(current_start_time)
        })

    return chunks

def time_output(time: int | None) -> str:
    if time is None:
        return "00:00:00"
    return f"{time // 3600000:02d}:{(time // 60000) % 60:02d}:{(time // 1000) % 60:02d}"

def sanitize_filename(name: str) -> str:
    safe_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    return safe_name

def get_video_title(url: str) -> str:
    """Fetch the YouTube video title."""
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict.get("title", "unnamed_video")
        except Exception as e:
            print(f"Error fetching video title: {e}")
            return "unnamed_video"

def create_json_file(url: str, scope: str, output_dir: str = "./json_output") -> str | None:
    transcript_data, selected_lang = get_youtube_transcript(url)

    if transcript_data:
        transcript = " ".join([x[1] for x in transcript_data])
        chunks = chunk_text(transcript_data)

        # Generate embeddings
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = embedder.encode(chunk_texts, convert_to_tensor=False).tolist()

        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding

        # Build JSON structure matching PDF handler
        json_data = {
            "type": "youtube",
            "scope": scope,
            "original_data": url,
            "extracted_text": transcript,
            "chunks": chunks
        }

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Use video title for filename
        video_title = get_video_title(url)
        safe_title = sanitize_filename(video_title)
        output_path = os.path.join(output_dir, f"{safe_title}.json")

        # Save JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

        print(f"JSON file created at: {output_path}")
        return output_path
    else:
        print("Failed to retrieve or process transcript.")
        return None

def main():
    url = "https://www.youtube.com/watch?v=_nuQ39Y4T5Q"
    scope = "test-scope"

    try:
        json_file = create_json_file(url, scope)
        if json_file:
            print(f"Generated JSON file: {json_file}")
        else:
            print("No JSON file generated.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main()