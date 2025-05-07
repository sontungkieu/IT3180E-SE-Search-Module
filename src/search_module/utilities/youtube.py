import yt_dlp
import json
import re
import os

def get_youtube_transcript(url, lang="en"):
    ydl_opts = {
        "quiet": True,
        "writesubtitles": True,
        "subtitleslangs": [lang, "en"],
        "skip_download": True,
        "extractor_args": {
            "youtube": {"player_client": ["web"]}
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get("title", "youtube_transcript")
            subtitles = info_dict.get("subtitles", {})
            automatic_captions = info_dict.get("automatic_captions", {})

            if lang in subtitles:
                subtitle_url = subtitles[lang][0]["url"]
            elif "en" in subtitles:
                subtitle_url = subtitles["en"][0]["url"]
            elif lang in automatic_captions:
                subtitle_url = automatic_captions[lang][0]["url"]
            elif "en" in automatic_captions:
                subtitle_url = automatic_captions["en"][0]["url"]
            else:
                print("No subtitles found")
                return None, title

            transcript = ydl.urlopen(subtitle_url).read().decode("utf-8")
            transcript_dict = json.loads(transcript)
            return extract_utf_from_events(transcript_dict), title

        except Exception as e:
            print(f"Error occurred while fetching subtitles: {e}")
            return None, "youtube_transcript"

def extract_utf_from_events(data):
    utf_scripts = []
    for event in data.get("events", []):
        if "segs" in event:
            utf_event = []
            for seg in event["segs"]:
                if "utf8" in seg and seg["utf8"].strip() != "":
                    utf_event.append(seg["utf8"].strip())
            if utf_event:
                utf_scripts.append([event["tStartMs"], " ".join(utf_event)])
    return utf_scripts

def chunk_text(data, chunk_size=250):
    chunks = []
    current_chunk = []
    current_chunk_word_count = 0
    current_start_time = None

    for start_time, text in data:
        words = text.split()
        for word in words:
            if current_chunk_word_count == chunk_size:
                chunks.append({
                    "location": time_output(current_start_time),
                    "text": " ".join(current_chunk)
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
            "location": time_output(current_start_time),
            "text": " ".join(current_chunk)
        })

    return chunks

def time_output(time_ms):
    hours = time_ms // 3600000
    minutes = (time_ms // 60000) % 60
    seconds = (time_ms // 1000) % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def sanitize_filename(name):
    name = name.strip().replace(" ", "_")
    return re.sub(r'[\\/*?:"<>|]', "", name)

def process_youtube(url = "http://youtube.com/watch?v=9vM4p9NN0Ts", scope= "IT3190E", lang="en"): # test hamf nayf
    transcript_data, title = get_youtube_transcript(url, lang)

    if transcript_data:
        transcript = " ".join([x[1] for x in transcript_data])
        chunks = chunk_text(transcript_data)
        for c_id in range(len(chunks)):
            chunks[c_id]["chunk_source"] = url
            chunks[c_id]["chunk_scope"] = scope
            chunks[c_id]["chunk_source_type"] = "youtube"
            chunks[c_id]["chunk_id"] = c_id + 1
        # print(chunks)
        return chunks, title
    else:
        return None, "youtube_transcript"

def quick_test_youtube():
    url = "https://www.youtube.com/watch?v=Rvppog1HZJY&t=3s"
    scope = "IT3190E"
    lang = "en"

    result, title = process_youtube(url, scope, lang)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Failed to extract transcript.")

def main():
    url = input("Paste the YouTube URL: ").strip()
    scope = input("Enter scope (e.g., topic, subject, or context): ").strip()
    lang = "en"

    result, title = process_youtube(url, scope, lang)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Create output directory if it doesn't exist
        output_dir = "json_output"
        os.makedirs(output_dir, exist_ok=True)

        # Sanitize filename
        safe_title = sanitize_filename(title)
        filename = f"{safe_title}.json"
        filepath = os.path.join(output_dir, filename)

        # Write JSON to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Transcript data saved to '{filepath}'.")
    else:
        print("Failed to extract transcript.")

if __name__ == "__main__":
    quick_test_youtube()
