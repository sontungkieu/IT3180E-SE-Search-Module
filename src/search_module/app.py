from search_module.utilities.youtube import process_youtube
from search_module.utilities.pdf import process_pdf
from search_module.utilities.db_helper import *
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

import json,os,base64

app = FastAPI()
db = VectorDatabase()
CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)


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
                chunks, title = process_youtube(json_data["data"],json_data['scope'])
                if not chunks:
                    return JSONResponse(content={
                        "status": "error",
                        "message": "Không thể xử lý Youtube URL"
                    }, status_code=500)


                for chunk in chunks:
                    db.add_chunk(chunk)
                if len(chunks) < 2:
                    return JSONResponse(content={
                        "status": "warning",
                        "message": "Độ dài transcript quá ngắn, có thể không đầy đủ hoặc bị lỗi.",
                        "first_chunk": chunks[0] if chunks else None
                    }, status_code=200)

                return JSONResponse(content={
                    "status": "success",
                    "message": "Youtube transcript added successfully",
                    "first_chunk": chunks[0]
                })


                # for chunk in chunks:
                #     db.add_chunk(chunk)
                
                
                # return JSONResponse(content={"status": "success", "message": "Youtube transcript added successfully"})
                #trả về add thành công
            elif json_data["add"] == "pdf":
                # 1. Giải mã base64
                pdf_bytes = base64.b64decode(json_data["data"])

                # 2. Xác định đường dẫn lưu file
                filename = json_data.get("filename", "uploaded.pdf")
                file_path = os.path.join(CACHE_DIR, filename)

                # 3. Ghi nội dung ra file
                with open(file_path, "wb") as f:
                    f.write(pdf_bytes)

                # 4. Gọi process_pdf với đường dẫn file
                chunks, title = process_pdf(pdf_path=file_path, scope=json_data["scope"])
                if not chunks:
                    return JSONResponse(content={
                        "status": "error",
                        "message": "Không thể xử lý PDF"
                    }, status_code=500)


                for chunk in chunks:
                    db.add_chunk(chunk)

                if len(chunks) < 2:
                    return JSONResponse(content={
                        "status": "warning",
                        "message": "Độ dài transcript quá ngắn, có thể không đầy đủ hoặc bị lỗi.",
                        "first_chunk": chunks[0] if chunks else None
                    }, status_code=200)

                return JSONResponse(content={"status": "success", "message": f"PDF '{filename}' added successfully","first_chunk": chunks[0]})

            else:
                #raise error : không hợp lệ
                # trả về erro và json error 
                return JSONResponse(content={"status": "error", "message": "Invalid add type"}, status_code=400)
        elif "search" in json_data:
            mod = json_data.get("mod","word")
            if mod not in ["word", "semantic"]:
                raise Exception()
            if mod == "word":
                print("word")
                tmp = db.word_search(json_data["search"], json_data["scope"])
                print(tmp)
                return tmp
            else: 
                return db.semantic_search(json_data["search"], json_data["scope"])
        return JSONResponse(content=result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Nội dung không phải là JSON hợp lệ")
