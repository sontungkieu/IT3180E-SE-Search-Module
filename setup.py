from setuptools import setup, find_packages

if __name__ == "__main__":
    setup()


# uvicorn src.search_module.app:app --port 8000

# streamlit run frontend.py
# https://labs.play-with-docker.com/
# docker build -t search-api .
# docker rm search-backend
# docker run -d -p 8000:8000 --name search-backend search-api
# docker ps
# docker logs -f search-backend
# docker save -o search-api.tar search-api:latest

# https://chatgpt.com/share/681b50a2-ea38-8009-89ec-25d9672a4b07

# docker load -i search-api.tar


