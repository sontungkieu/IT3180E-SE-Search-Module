from search_module.utilities.youtube import process_youtube
from search_module.utilities.pdf import process_pdf
from search_module.utilities.db_helper import *
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

import json

app = FastAPI()
db = VectorDatabase()

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
                chunks, title = process_youtube({"url": json_data["data"], "scope":json_data['scope']})
                for chunk in chunks:
                    db.add_chunk(chunk)
                return JSONResponse(content={"status": "success", "message": "Youtube transcript added successfully"})
                #trả về add thành công
            elif json_data["add"] == "pdf":
                chunks, title = process_pdf(pdf_data=json_data["data"],scope=json_data["scope"])
                for chunk in chunks:
                    db.add_chunk(chunk)
                return JSONResponse(content={"status": "success", "message": "PDF added successfully"})
                #trả về add thành công
            else:
                #raise error : không hợp lệ
                # trả về erro và json error 
                return JSONResponse(content={"status": "error", "message": "Invalid add type"}, status_code=400)
        elif "search" in json_data:
            mod = json_data.get("mod","word")
            if mod not in ["word", "semantic"]:
                raise Exception()
            if mod == "word":
                return db.word_search(json_data["data"], json_data["scope"])
            else: 
                return db.semantic_search(json_data["data"], json_data["scope"])
        return JSONResponse(content=result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Nội dung không phải là JSON hợp lệ")
