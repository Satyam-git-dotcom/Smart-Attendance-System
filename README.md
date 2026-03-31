# 🛡️ Smart Attendance System with Anti-Spoofing

A professional, AI-powered attendance solution utilizing **Face Recognition (Dlib/FaceNet)** and **Liveness Detection (Blink Detection)** to ensure secure and efficient tracking. Optimized for modern macOS environments (Apple Silicon).

## 🚀 Key Features
- **Real-Time Identification**: High-accuracy face recognition using the `face_recognition` library.
- **Anti-Spoofing (Liveness)**: Prevents "Photo-Spoofing" and "Video-Spoofing" by requiring students to blink (Eye Aspect Ratio method).
- **ID-Based Tracking**: Every user is tracked by both Name and a unique Registration Number.
- **Administrative Dashboard**: 
    - **Live Tracker**: Monitor high-FPS attendance with visual feedback.
    - **Manage Users**: Search, edit, and delete registered users from the UI.
    - **Attendance History**: View, filter, and export detailed logs (CSV).
- **Secure Persistence**: Centralized SQLite database for managing all records.

## 🛠️ Tech Stack
- **Languages**: Python 3.x
- **Computer Vision**: OpenCV, Dlib, face_recognition
- **User Interface**: Streamlit
- **Data Layer**: SQLite3, Pandas
- **Models**: HOG Detector, 68-Facial Landmark Predictor, ResNet-34 Face Embedding

## 📦 Installation & Setup

### 1. System Dependencies (macOS)
Before setting up the Python environment, ensure you have the required build tools for **Dlib**:
```bash
brew install cmake boost libpng jpeg-turbo
```

### 2. Environment Setup
Clone the repository and install the dependencies:
```bash
git clone https://github.com/[your-username]/smart-attendance-system.git
cd smart-attendance-system
pip install -r requirements.txt
```

### 3. Required Models
Download the facial landmark predictor and place it in the project root:
- [shape_predictor_68_face_landmarks.dat](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2) (Extract the `.bz2` file after downloading).

## 🏃 Usage Guide

### Phase 1: User Registration
To register a new student or employee:
1.  Run the CLI registration script:
    ```bash
    python3 register.py
    ```
2.  Enter the user's **Name** and **Registration Number**.
3.  Look at the webcam and move your head slowly as the system captures 20 reference images.
4.  The system will automatically generate the required face encodings.

### Phase 2: Attendance Tracking
To launch the attendance and management dashboard:
1.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
2.  Select **"Attendance Tracker"** from the sidebar.
3.  Each person stands in front of the camera and **blinks** to confirm their identity.
4.  Check the **"Attendance History"** tab to view or download the logs.

## 📂 Project Structure
```text
.
├── app.py                # Main Streamlit Dashboard
├── register.py           # CLI User Registration
├── src/
│   ├── liveness.py       # EAR Blink Detection logic
│   ├── recognize.py      # Face Identification logic
│   └── attendance.py     # Database & History Management
├── dataset/              # User Face Datasets (Ignored by Git)
├── encodings/            # Generated Face Models (Ignored by Git)
├── attendance.db         # SQLite Database (Ignored by Git)
└── requirements.txt      # Project Dependencies
```
