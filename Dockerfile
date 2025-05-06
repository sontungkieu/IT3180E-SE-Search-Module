# # Base image
# FROM python:3.13-alpine3.21

# # Set working directory
# WORKDIR /app

# # Copy dependency files
# COPY requirements.txt .

# # Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy application files
# COPY . .

# # Expose port
# EXPOSE 8000

# # Command to run the application
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
# Sử dụng base image nhẹ nhưng đầy đủ hơn Alpine
FROM python:3.10-slim

# Cập nhật & cài các gói cần thiết cho xử lý PDF, Youtube
RUN apt-get update && apt-get install -y \
    ffmpeg \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục làm việc
WORKDIR /app

# Sao chép requirements
COPY requirements.txt .

# Cài đặt Python dependencies
# RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
# RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
#  && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
# RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt


# Sao chép toàn bộ source code
COPY . .
ENV PYTHONPATH=/app/src


# Mở port FastAPI
EXPOSE 8000

# Chạy app (chỉ định đúng path tới app.py trong src)
CMD ["uvicorn", "src.search_module.app:app", "--host", "0.0.0.0", "--port", "8000"]
