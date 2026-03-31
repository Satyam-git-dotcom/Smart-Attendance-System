# 🛡️ Smart Attendance System with Classroom Management

A professional, AI-powered attendance solution utilizing **Face Recognition (Dlib)** and **Liveness Detection (Blink Detection)**. This system is designed for teachers and administrators to manage multiple courses, students, and attendance logs through a single, intuitive dashboard.

## 🚀 Key Features
- **Classroom Management**: Organize students by **Course/Class** (e.g., "Math 101", "Computer Vision").
- **Native UI Registration**: Register students with 20-frame face capture directly in the web dashboard—no terminal commands required!
- **Anti-Spoofing (Liveness)**: Prevents photo or video fraud by requiring a physical **Blink** (Eye Aspect Ratio method) to confirm attendance.
- **Flexible Tracking**: Supports multiple entries per day with a **5-minute cooldown** to prevent duplicate flooding.
- **Administrative Control**:
    - **Manage Students**: Edit profile details, change courses, or permanently remove students and their datasets.
    - **Log Deletion**: Delete individual attendance entries if recorded by mistake without affecting student records.
    - **Advanced Filtering**: Filter history by Course, Name, or Date and export reports to **CSV**.

## 🛠️ Tech Stack
- **Languages**: Python 3.x
- **Computer Vision**: OpenCV, Dlib, face_recognition
- **User Interface**: Streamlit
- **Data Layer**: SQLite3, Pandas
- **Aesthetics**: Premium Dark/Modern UI with interactive feedback and animations.

## 📦 Installation & Setup

### 1. System Dependencies (macOS)
Dlib requires C++ build tools. Install them via Homebrew:
```bash
brew install cmake boost libpng jpeg-turbo
```

### 2. Environment Setup
Clone the repository and install the Python dependencies:
```bash
git clone https://github.com/[your-username]/smart-attendance-system.git
cd smart-attendance-system
pip install -r requirements.txt
```

### 3. Required Models
Download the facial landmark predictor and place it in the project root:
- [shape_predictor_68_face_landmarks.dat](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2)

## 🏃 Usage Guide

1. **Launch the Dashboard**:
   ```bash
   streamlit run app.py
   ```
2. **Phase 1: Registration**: Go to **"Register User"**, enter the Student Name, ID, and **Course**, then start the live capture.
3. **Phase 2: Attendance**: Students stand in front of the **"Attendance Tracker"** and blink. The success message confirms their name and class.
4. **Phase 3: Management**: Use **"Attendance History"** to filter by course or delete specific incorrect logs.

## 📂 Project Structure
```text
.
├── app.py                # Main Dashboard (Tracker, History, Registration, Management)
├── src/
│   ├── liveness.py       # EAR Blink Detection logic
│   ├── recognize.py      # Face Identification & Encoding logic
│   └── attendance.py     # Database Schema & Classroom logic
├── dataset/              # Student Image Datasets (Local only)
├── encodings/            # AI Model Encodings (Local only)
├── attendance.db         # SQLite Database (Local only)
└── requirements.txt      # Dependencies
```
