import streamlit as st
import cv2
import numpy as np
import dlib
import os
from src.liveness import check_liveness
from src.recognize import load_encodings, recognize_face, encode_faces
from src.attendance import init_db, mark_attendance, get_attendance_history, get_registered_users, delete_user_db, update_user_db
import pandas as pd
import time
import shutil

# Constants for dlib landmarks (68 landmarks model)
EYE_AR_THRESH = 0.2
EYE_AR_CONSEC_FRAMES = 3
LEFT_EYE_INDICES = [36, 37, 38, 39, 40, 41]
RIGHT_EYE_INDICES = [42, 43, 44, 45, 46, 47]

# Initialize DB
init_db()

# Streamlit UI Configuration
st.set_page_config(page_title="Smart Attendance System", layout="wide")
st.title("🛡️ Smart Attendance with Anti-Spoofing")

# Sidebar for navigation
sidebar = st.sidebar.radio("Navigation", ["Attendance Tracker", "Attendance History", "Register User", "Manage Users"])

# Load known face encodings
known_data = load_encodings()

if sidebar == "Attendance Tracker":
    st.subheader("Real-Time Face Recognition & Liveness Detection")
    
    # Placeholder for webcam feed
    frame_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Load dlib facial landmark predictor
    # Note: Requires shape_predictor_68_face_landmarks.dat in root
    predictor_path = "shape_predictor_68_face_landmarks.dat"
    if not os.path.exists(predictor_path):
        st.error(f"Error: Predictor file '{predictor_path}' not found. Please download it from dlib.net.")
        st.stop()
        
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    # State variables
    blink_counter = 0
    total_blinks = 0
    cap = cv2.VideoCapture(0)

    stop_button = st.button("Stop Attendance")

    while cap.isOpened() and not stop_button:
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            st.warning("Webcam frame skipped. Trying again...")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Face Recognition (Perform once per frame for all faces)
        face_locations, face_names = recognize_face(frame, known_data)

        # dlib face detection
        rects = detector(gray, 0)

        for i, rect in enumerate(rects):
            shape = predictor(gray, rect)
            shape_np = np.array([[p.x, p.y] for p in shape.parts()])

            # Check liveness (blink detection)
            is_blinking, ear = check_liveness(shape_np, LEFT_EYE_INDICES, RIGHT_EYE_INDICES, EYE_AR_THRESH)

            if is_blinking:
                blink_counter += 1
            else:
                if blink_counter >= EYE_AR_CONSEC_FRAMES:
                    total_blinks += 1
                blink_counter = 0

            # Liveness status
            liveness_status = "Real" if total_blinks > 0 else "Pending Liveness (Blink!)"
            color = (0, 255, 0) if liveness_status == "Real" else (0, 0, 255)

            # Draw feedback on frame
            (x, y, w, h) = (rect.left(), rect.top(), rect.width(), rect.height())
            
            # Simple heuristic: assign the name from recognize_face based on index or position
            # Since both use dlib/face_recognition, indices often align but we can use coordinates for robustness
            # Simple heuristic: assign the name from recognize_face based on index or position
            name = "Unknown"
            if i < len(face_names):
                name = face_names[i]

            # Split name and reg_no for cleaner UI display
            display_name = name
            if "_" in name:
                n, r = name.split("_", 1)
                display_name = f"{n} (Reg: {r})"
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"Liveness: {liveness_status}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.putText(frame, f"ID: {display_name}", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Mark attendance if real and recognized
            if liveness_status == "Real" and name != "Unknown":
                success, msg = mark_attendance(name)
                if success:
                    st.toast(f"✅ {msg} for {display_name}")
                # Reset blink for next person or next session
                # total_blinks = 0 

        # Display the frame in Streamlit
        frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)

    cap.release()

elif sidebar == "Attendance History":
    st.subheader("📋 Detailed Attendance Log")
    history = get_attendance_history()
    if history:
        # history returns (name, reg_no, date, time, status)
        df = pd.DataFrame(history, columns=["Name", "Reg Number", "Date", "Time", "Status"])
        st.dataframe(df, use_container_width=True)
        
        # Download as CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Report (CSV)", data=csv, file_name="attendance_report.csv", mime="text/csv")
    else:
        st.info("No attendance records found yet.")

elif sidebar == "Register User":
    st.subheader("📝 Register a New User")
    st.info("Registration requires both a **Name** and a **Registration Number**. For security and stability, the registration window will open in your terminal/console.")
    
    if st.button("Launch Registration Terminal"):
        st.warning("Please check your terminal to enter the user details.")
        # We don't use subprocess here because it's hard to handle interactive terminal input via Streamlit buttons
        # Instead, we guide the user to run the script manually.
        st.code("python3 register.py", language="bash")

elif sidebar == "Manage Users":
    st.subheader("👥 User Management Dashboard")
    users = get_registered_users()
    
    if users:
        df_users = pd.DataFrame(users, columns=["Name", "Reg Number", "Registered At"])
        st.dataframe(df_users, use_container_width=True)
        
        st.divider()
        st.write("### Actions")
        
        # Select user to manage
        user_list = [f"{u[0]} ({u[1]})" for u in users]
        selected_user_str = st.selectbox("Select user to Edit or Delete", ["-- Select User --"] + user_list)
        
        if selected_user_str != "-- Select User --":
            # Extract reg_no from the selection string "Name (RegNo)"
            selected_reg_no = selected_user_str.split("(")[-1].strip(")")
            selected_user_data = next(u for u in users if u[1] == selected_reg_no)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### 📝 Edit User Info")
                edit_name = st.text_input("New Name", value=selected_user_data[0])
                edit_reg = st.text_input("New Registration Number", value=selected_user_data[1])
                
                if st.button("Save Changes"):
                    if edit_name and edit_reg:
                        # Rename dataset folder
                        old_identity = f"{selected_user_data[0]}_{selected_user_data[1]}"
                        new_identity = f"{edit_name}_{edit_reg}"
                        
                        old_path = os.path.join("dataset", old_identity)
                        new_path = os.path.join("dataset", new_identity)
                        
                        success = True
                        if os.path.exists(old_path):
                            try:
                                os.rename(old_path, new_path)
                            except Exception as e:
                                st.error(f"Error renaming dataset folder: {e}")
                                success = False
                        
                        if success:
                            if update_user_db(selected_user_data[1], edit_name, edit_reg):
                                st.success("Database updated! Re-generating encodings...")
                                encode_faces()
                                st.rerun()
                            else:
                                st.error("Error updating database. Registration Number might already exist.")
                    else:
                        st.warning("Please fill in both fields.")

            with col2:
                st.write("#### 🗑️ Delete User")
                st.warning(f"Are you sure you want to delete {selected_user_data[0]}?")
                if st.button("Confirm Delete", type="primary"):
                    # Delete dataset folder
                    identity = f"{selected_user_data[0]}_{selected_user_data[1]}"
                    path = os.path.join("dataset", identity)
                    
                    if os.path.exists(path):
                        shutil.rmtree(path)
                    
                    # Delete from DB
                    delete_user_db(selected_user_data[1])
                    
                    st.success("User deleted! Re-generating encodings...")
                    encode_faces()
                    st.rerun()
    else:
        st.info("No registered users found.")
