# FROM python:3.10-slim

# WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     ffmpeg \
#     libgl1 \
#     libglib2.0-0 \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# ENV PYTHONUNBUFFERED=1

# CMD ["streamlit", "run", "dashbord/dashbord_app.py", "--server.address=0.0.0.0", "--server.port=8501"]

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --default-timeout=300 --retries 10 --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "dashbord/dashbord_app.py", "--server.address=0.0.0.0", "--server.port=8501"]