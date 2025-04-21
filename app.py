from add_document.youtube_handler import process_youtube
from add_document.pdf_handler import process_pdf

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

import json

app = FastAPI()

@app.post("/")
async def aggregate_function(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail= "File cần phải có định dạng .json!")
    try: 
        contents = await file.read()

        json_data = json.loads(contents.decode("utf-8"))
        # Xử lý JSON ở đây (ví dụ: in ra nội dung)
        print("Dữ liệu nhận được:", json_data)

        # Giả sử ta chỉ muốn trả lại số lượng keys trong JSON
        result = {
            "received_keys": list(json_data.keys()),
            "num_keys": len(json_data)
        }


        if "add" in json_data:
            if json_data["add"] == "youtube":
                process_youtube(url = json_data["data"], scope=json_data['scope'])
            elif json_data["add"] == "pdf":
                process_pdf(pdf_data=json_data["data"],scope=json_data["scope"])
            else:
                #raise error : không hợp lệ 
                pass
        elif "search" in json_data:
            mod = json_data.get("mod","word")
            if mod not in ["word", "semantic"]:
                raise Exception()
            if mod == "word":
                # search_word()
                pass
            else: 
                # search_semantic()
                pass
        return JSONResponse(content=result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Nội dung không phải là JSON hợp lệ")
