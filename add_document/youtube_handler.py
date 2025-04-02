import yt_dlp


def get_youtube_transcript(url, lang="vi"):
    """
    Lấy transcript (phụ đề) từ video YouTube.
    Nếu không có phụ đề trong ngôn ngữ yêu cầu, tìm phụ đề tự động tiếng Việt và Anh.
    """
    ydl_opts = {
        "quiet": True,  # Tắt log chi tiết
        "writesubtitles": True,  # Ghi lại phụ đề nếu có
        "subtitleslangs": [
            lang,
            "en",
        ],  # Lấy phụ đề theo ngôn ngữ yêu cầu, mặc định tiếng việt, nếu không có thì thử 'en'
        "skip_download": True,  # Không tải video, chỉ tải phụ đề
        "extractor_args": {
            "youtube": {"player_client": ["web"]}
        },  # Sử dụng client web để lấy phụ đề
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Lấy thông tin video
            info_dict = ydl.extract_info(url, download=False)

            # Lấy các phụ đề
            subtitles = info_dict.get("subtitles", {})
            automatic_captions = info_dict.get("automatic_captions", {})

            # Kiểm tra và lấy phụ đề theo ngôn ngữ yêu cầu
            if lang in subtitles:
                subtitle_url = subtitles[lang][0]["url"]  # Lấy URL phụ đề từ dict
            elif "en" in subtitles:
                subtitle_url = subtitles["en"][0]["url"]  # Lấy URL phụ đề từ dict
            elif lang in automatic_captions:
                subtitle_url = automatic_captions[lang][0][
                    "url"
                ]  # Fallback vào phụ đề yêu cầu
            elif "en" in automatic_captions:
                subtitle_url = automatic_captions["en"][0][
                    "url"
                ]  # Fallback vào phụ đề tiếng Anh
            else:
                print("No subtitles found")
                return None

            # Tải dữ liệu phụ đề
            import json

            transcript = ydl.urlopen(subtitle_url).read().decode("utf-8")
            transcript_dict = json.loads(transcript)
            return extract_utf_from_events(transcript_dict)

        except Exception as e:
            print(f"Error occurred while fetching subtitles: {e}")
            return None


def extract_utf_from_events(data):
    utf_scripts = []

    for event in data["events"]:
        if "segs" in event:
            utf_event = []
            for seg in event["segs"]:
                if "utf8" in seg:
                    if seg["utf8"] != "\n":
                        utf_event.append(seg["utf8"])
            if utf_event:
                utf_scripts.append([event["tStartMs"], " ".join(utf_event)])

    return utf_scripts


def process_youtube(url, scope, lang="en"):
    """
    Xử lý URL YouTube: lấy transcript, tạo JSON chứa dữ liệu
    """
    transcript_data = get_youtube_transcript(url, lang)

    if transcript_data:
        transcript = " ".join([x[1] for x in transcript_data])

        # Chia transcript thành các đoạn nhỏ
        chunks = chunk_text(transcript_data)

        # Tạo cấu trúc JSON với metadata
        document_data = {
            "type": "youtube",
            "scope": scope,
            "original_data": url,
            "extracted_text": transcript,
            "chunks": chunks,
        }

        return document_data
    else:
        return None


def chunk_text(data, chunk_size=250):
    """
    Chia các data seg vào các chunk sao cho tổng số từ trong các chunk là 300.
    Thêm timestamp đầu mỗi chunk.
    """
    chunks = []
    current_chunk = []
    current_chunk_word_count = 0
    current_start_time = None

    for start_time, text in data:
        words = text.split()
        for word in words:
            if current_chunk_word_count == chunk_size:
                chunks.append(
                    {
                        "timestamp": time_output(current_start_time),
                        "text": " ".join(current_chunk),
                    }
                )
                current_chunk = []
                current_chunk_word_count = 0
                current_start_time = None

            if current_start_time is None:
                current_start_time = start_time

            current_chunk.append(word)
            current_chunk_word_count += 1

    if current_chunk:
        chunks.append(
            {
                "timestamp": time_output(current_start_time),
                "text": " ".join(current_chunk),
            }
        )

    return chunks


def words_count(text):
    """
    Đếm số từ trong văn bản.
    """
    return len(text.split())


def time_output(time):
    return f"{time // 3600000:02d}:{(time // 60000) % 60:02d}:{(time // 1000) % 60:02d}"
