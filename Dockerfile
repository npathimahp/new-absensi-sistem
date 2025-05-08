# Gunakan image base Python
FROM python:3.9-slim

# Install CMake dan build tools
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies dari requirements.txt
COPY requirements.txt /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin aplikasi ke dalam container
COPY . /app

# Jalankan aplikasi
CMD ["python", "run.py"]
