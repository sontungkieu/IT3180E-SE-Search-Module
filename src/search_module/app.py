# from search_module.utilities.youtube import process_youtube
# from search_module.utilities.pdf import process_pdf
# from search_module.utilities.db_helper import *
# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.responses import JSONResponse

# import json,os,base64

# app = FastAPI()
# db = VectorDatabase()
# CACHE_DIR = "./cache"
# os.makedirs(CACHE_DIR, exist_ok=True)


# @app.post("/")
# async def aggregate_function(file: UploadFile = File(...)):
#     if not file.filename.endswith(".json"):
#         raise HTTPException(status_code=400, detail= "File cần phải có định dạng .json!")
#     try: 
#         contents = await file.read()

#         json_data = json.loads(contents.decode("utf-8"))
#         # Xử lý JSON ở đây (ví dụ: in ra nội dung)
#         print("Dữ liệu nhận được:", json_data)

#         # Giả sử ta chỉ muốn trả lại số lượng keys trong JSON
#         result = {
#             "received_keys": list(json_data.keys()),
#             "num_keys": len(json_data)
#         }


#         if "add" in json_data:
#             if json_data["add"] == "youtube":
#                 chunks, title = process_youtube(json_data["data"],json_data['scope'])
#                 if not chunks:
#                     return JSONResponse(content={
#                         "status": "error",
#                         "message": "Không thể xử lý Youtube URL"
#                     }, status_code=500)


#                 for chunk in chunks:
#                     if chunk["chunk_scope"] is None:
#                         raise HTTPException(status_code=400, detail="Chunk scope không hợp lệ")
#                     db.add_chunk(chunk)
#                 if len(chunks) < 2:
#                     return JSONResponse(content={
#                         "status": "warning",
#                         "message": "Độ dài transcript quá ngắn, có thể không đầy đủ hoặc bị lỗi.",
#                         "first_chunk": chunks[0] if chunks else None
#                     }, status_code=200)

#                 return JSONResponse(content={
#                     "status": "success",
#                     "message": "Youtube transcript added successfully",
#                     "first_chunk": chunks[0]
#                 })

#             elif json_data["add"] == "pdf":
#                 # 1. Giải mã base64
#                 pdf_bytes = base64.b64decode(json_data["data"])

#                 # 2. Xác định đường dẫn lưu file
#                 filename = json_data.get("filename", "uploaded.pdf")
#                 file_path = os.path.join(CACHE_DIR, filename)

#                 # 3. Ghi nội dung ra file
#                 with open(file_path, "wb") as f:
#                     f.write(pdf_bytes)

#                 # 4. Gọi process_pdf với đường dẫn file
#                 chunks, title = process_pdf(pdf_path=file_path, scope=json_data["scope"])
#                 if not chunks:
#                     return JSONResponse(content={
#                         "status": "error",
#                         "message": "Không thể xử lý PDF"
#                     }, status_code=500)


#                 for chunk in chunks:
#                     db.add_chunk(chunk)

#                 if len(chunks) < 2:
#                     return JSONResponse(content={
#                         "status": "warning",
#                         "message": "Độ dài transcript quá ngắn, có thể không đầy đủ hoặc bị lỗi.",
#                         "first_chunk": chunks[0] if chunks else None
#                     }, status_code=200)

#                 return JSONResponse(content={"status": "success", "message": f"PDF '{filename}' added successfully","first_chunk": chunks[0]})

#             else:
#                 #raise error : không hợp lệ
#                 # trả về erro và json error 
#                 return JSONResponse(content={"status": "error", "message": "Invalid add type"}, status_code=400)
#         elif "search" in json_data:
#             mod = json_data.get("mod","word")
#             if mod not in ["word", "semantic"]:
#                 raise Exception()
#             if mod == "word":
#                 print("word")
#                 tmp = db.word_search(json_data["search"], json_data["scope"])
#                 print(tmp)
#                 return tmp
#             else: 
#                 return db.semantic_search(json_data["search"], json_data["scope"])
#         return JSONResponse(content=result)
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Nội dung không phải là JSON hợp lệ")


from search_module.utilities.youtube import process_youtube
from search_module.utilities.pdf import process_pdf
from search_module.utilities.db_helper import *
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

import json
import os
import base64
import hashlib

app = FastAPI()
db = VectorDatabase()
CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)


@app.post("/")
async def aggregate_function(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File cần phải có định dạng .json!")

    try:
        contents = await file.read()
        json_data = json.loads(contents.decode("utf-8"))

        # Kiểm tra trường "user"
        user = json_data.get("user")
        if not user:
            raise HTTPException(status_code=400, detail="Missing 'user' field in JSON")

        # Tạo salted_user: username + phần đầu của sha256(username) sao cho đủ 20 kí tự
        hash_hex = hashlib.sha256(user.encode("utf-8")).hexdigest()
        if len(user) >= 20:
            salted_user = user[:20]
        else:
            needed = 20 - len(user)
            salted_user = user + hash_hex[:needed]

        # Tạo folder cho user bên trong CACHE_DIR
        user_dir = os.path.join(CACHE_DIR, salted_user)
        os.makedirs(user_dir, exist_ok=True)

        # Gán lại scope = original_scope + "_" + salted_user
        original_scope = json_data.get("scope", "")
        new_scope = f"{original_scope}_{salted_user}"

        print("Dữ liệu nhận được:", json_data)
        print(f"Salted user: {salted_user}, New scope: {new_scope}")

        # Khởi tạo kết quả mặc định (chỉ trả về các key trong JSON và số lượng key)
        result = {
            "received_keys": list(json_data.keys()),
            "num_keys": len(json_data)
        }

        if "add" in json_data:
            if json_data["add"] == "youtube":
                # Xử lý YouTube với new_scope
                chunks, title = process_youtube(json_data["data"], new_scope)
                if not chunks:
                    return JSONResponse(
                        content={"status": "error", "message": "Không thể xử lý Youtube URL"},
                        status_code=500
                    )

                for chunk in chunks:
                    if chunk.get("chunk_scope") is None:
                        raise HTTPException(status_code=400, detail="Chunk scope không hợp lệ")
                    db.add_chunk(chunk)

                if len(chunks) < 2:
                    return JSONResponse(
                        content={
                            "status": "warning",
                            "message": "Độ dài transcript quá ngắn, có thể không đầy đủ hoặc bị lỗi.",
                            "first_chunk": chunks[0] if chunks else None
                        },
                        status_code=200
                    )

                return JSONResponse(
                    content={
                        "status": "success",
                        "message": "Youtube transcript added successfully",
                        "first_chunk": chunks[0]
                    }
                )

            elif json_data["add"] == "pdf":
                # 1. Giải mã base64
                pdf_bytes = base64.b64decode(json_data["data"])

                # 2. Xác định đường dẫn lưu file: lưu vào folder của user
                filename = json_data.get("filename", "uploaded.pdf")
                file_path = os.path.join(user_dir, filename)

                # 3. Ghi nội dung ra file
                with open(file_path, "wb") as f:
                    f.write(pdf_bytes)

                # 4. Gọi process_pdf với đường dẫn file và new_scope
                chunks, title = process_pdf(pdf_path=file_path, scope=new_scope)
                if not chunks:
                    return JSONResponse(
                        content={"status": "error", "message": "Không thể xử lý PDF"},
                        status_code=500
                    )

                for chunk in chunks:
                    db.add_chunk(chunk)

                if len(chunks) < 2:
                    return JSONResponse(
                        content={
                            "status": "warning",
                            "message": "Độ dài transcript quá ngắn, có thể không đầy đủ hoặc bị lỗi.",
                            "first_chunk": chunks[0] if chunks else None
                        },
                        status_code=200
                    )

                return JSONResponse(
                    content={
                        "status": "success",
                        "message": f"PDF '{filename}' added successfully",
                        "first_chunk": chunks[0]
                    }
                )

            else:
                return JSONResponse(
                    content={"status": "error", "message": "Invalid add type"},
                    status_code=400
                )

        elif "search" in json_data:
            # Gán lại new_scope cho search
            mod = json_data.get("mod", "word")
            if mod not in ["word", "semantic"]:
                raise HTTPException(status_code=400, detail="Invalid search mode")

            if mod == "word":
                tmp = db.word_search(json_data["search"], new_scope)
                return tmp
            else:
                return db.semantic_search(json_data["search"], new_scope)

        # Nếu không phải "add" hay "search", trả về thông tin về keys
        return JSONResponse(content=result)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Nội dung không phải là JSON hợp lệ")
