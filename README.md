# Face Recognition Attendance System
This project is a face recognition attendance system that uses the face_recognition library to recognize faces and OpenCV to capture images.

## Requirements
- Python 3.10

## Installation
1. Create a virtual environment
```bash
python -m venv venv
```

2. Activate the virtual environment
```bash
# Windows
venv\Scripts\activate

# Linux / MacOS
source venv/bin/activate
```

3. Install the required packages
```bash
pip install -r requirements.txt
```

## Usage
1. Run the encode_faces.py script to encode the faces of the people you want to recognize.
```bash
python misc/initial_encoder.py
```

2. Run the web app
```bash
python run.py
```

3. Open your browser and go to http://localhost:5000

4. To stop the web app, press `Ctrl + C` in the terminal.
