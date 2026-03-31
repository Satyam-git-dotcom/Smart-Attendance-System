import streamlit as st
import cv2
import numpy as np
import dlib
import os
from src.liveness import check_liveness
from src.recognize import load_encodings, recognize_face, encode_faces
from src.attendance import (
    init_db, mark_attendance, get_attendance_history, 
    get_registered_users, delete_user_db, update_user_db, 
    register_user_db, delete_attendance_log
)
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
st.title("🛡️ Smart Attendance with Classroom Management")

# Sidebar for navigation
sidebar = st.sidebar.radio("Navigation", ["Attendance Tracker", "Attendance History", "Register User", "Manage Users"])

# Load known face encodings
known_data = load_encodings()

if sidebar == "Attendance Tracker":
    st.subheader("Real-Time Face Recognition & Course Logging")
    
    # Placeholder for webcam feed
    st.info("💡 Stand in front of the camera and **blink** to record your attendance.")
    attendance_popup_placeholder = st.empty()
    frame_placeholder = st.empty()
    status_placeholder = st.empty()
    
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
        
        # Face Recognition
        face_locations, face_names = recognize_face(frame, known_data)
        rects = detector(gray, 0)

        for i, rect in enumerate(rects):
            shape = predictor(gray, rect)
            shape_np = np.array([[p.x, p.y] for p in shape.parts()])

            # Check liveness
            is_blinking, ear = check_liveness(shape_np, LEFT_EYE_INDICES, RIGHT_EYE_INDICES, EYE_AR_THRESH)

            if is_blinking:
                blink_counter += 1
            else:
                if blink_counter >= EYE_AR_CONSEC_FRAMES:
                    total_blinks += 1
                blink_counter = 0

            liveness_status = "Real" if total_blinks > 0 else "Pending Liveness (Blink!)"
            color = (0, 255, 0) if liveness_status == "Real" else (0, 0, 255)

            (x, y, w, h) = (rect.left(), rect.top(), rect.width(), rect.height())
            name = face_names[i] if i < len(face_names) else "Unknown"
            display_name = name.split("_")[0] if "_" in name else name
            
            # Label overlay
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{display_name} - {liveness_status}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Mark attendance if real and recognized
            if liveness_status == "Real" and name != "Unknown":
                success, msg = mark_attendance(name)
                if success:
                    attendance_popup_placeholder.success(f"🎉 {msg}: {display_name}")
                else:
                    if "Already recorded" in msg:
                        attendance_popup_placeholder.warning(f"🕒 {msg}")
                    else:
                        st.toast(f"❌ {msg}")
        
        frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)

    cap.release()

elif sidebar == "Attendance History":
    st.subheader("📋 Detailed Attendance Log")
    history = get_attendance_history()
    
    if history:
        # columns: ["Name", "Reg Number", "Course", "Date", "Time", "Status", "rowid"]
        df = pd.DataFrame(history, columns=["Name", "Reg Number", "Course", "Date", "Time", "Status", "RowID"])
        
        # Course Filter
        courses = ["All"] + sorted(list(set(df["Course"].dropna().tolist())))
        selected_course = st.selectbox("Filter by Course", courses)
        
        filtered_df = df if selected_course == "All" else df[df["Course"] == selected_course]
        
        # Display the table (without internal rowid)
        st.dataframe(filtered_df.drop(columns=["RowID"]), use_container_width=True)
        
        # Log Management (Deletion)
        st.divider()
        st.write("### 🗑️ Manage Individual Logs")
        log_list = [f"{row['Date']} {row['Time']} - {row['Name']} ({row['Course']})" for idx, row in filtered_df.iterrows()]
        selected_log_str = st.selectbox("Select a log entry to remove", ["-- Select Entry --"] + log_list)
        
        if selected_log_str != "-- Select Entry --":
            # Find the RowID using the index
            log_idx = log_list.index(selected_log_str)
            target_rowid = filtered_df.iloc[log_idx]["RowID"]
            
            if st.button("Delete This Entry", type="primary"):
                if delete_attendance_log(target_rowid):
                    st.success("Entry removed from history.")
                    st.rerun()
                else:
                    st.error("Error removing entry.")
        
        # Download as CSV
        csv = filtered_df.drop(columns=["RowID"]).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report (CSV)", data=csv, file_name=f"attendance_{selected_course}.csv", mime="text/csv")
    else:
        st.info("No attendance records found yet.")

elif sidebar == "Register User":
    st.subheader("📝 New Student Registration")
    st.info("Register a student into a specific class. Capture 20 images for the AI model.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        reg_name = st.text_input("Full Name")
    with col2:
        reg_id = st.text_input("Registration ID")
    with col3:
        reg_course = st.text_input("Course Name (e.g., Math 101)")
    
    if st.button("📷 Start Live Capture", use_container_width=True):
        if reg_name and reg_id and reg_course:
            identity = f"{reg_name}_{reg_id}"
            save_path = os.path.join("dataset", identity)
            if not os.path.exists(save_path): os.makedirs(save_path)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            frame_placeholder = st.empty()
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            cap = cv2.VideoCapture(0)
            count = 0
            while count < 20:
                ret, frame = cap.read()
                if not ret: break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                display_frame = frame.copy()
                for (x, y, w, h) in faces:
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    count += 1
                    cv2.imwrite(f"{save_path}/{identity}_{count}.jpg", frame[y:y+h, x:x+w])
                    progress_bar.progress(count / 20)
                    status_text.text(f"Capturing: {count}/20 images...")
                    time.sleep(0.3)
                
                frame_placeholder.image(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
                if count >= 20: break
            
            cap.release()
            frame_placeholder.empty()
            
            if register_user_db(reg_name, reg_id, reg_course):
                with st.spinner("Optimizing AI model for new student..."):
                    encode_faces()
                    st.success(f"✅ {reg_name} registered for {reg_course}!")
            else:
                st.error("Registration ID already exists.")
        else:
            st.warning("Please fill in all 3 fields (Name, ID, and Course).")

elif sidebar == "Manage Users":
    st.subheader("👥 Student & Class Records")
    users = get_registered_users()
    
    if users:
        # columns: [Name, RegNo, Date, RowID, Course]
        display_data = [[u[0], u[1], u[4], u[2]] for u in users]
        df_users = pd.DataFrame(display_data, columns=["Name", "Reg ID", "Course", "Joined At"])
        st.dataframe(df_users, use_container_width=True)
        
        st.divider()
        st.write("### ⚙️ Edit Records")
        user_ids = [f"{u[0]} ({u[4]}) [ID: {u[1]}]" for u in users]
        selection = st.selectbox("Select student to Manage", ["-- Select Student --"] + user_ids)
        
        if selection != "-- Select Student --":
            user_idx = user_ids.index(selection)
            selected_user_data = users[user_idx]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("#### 📝 Edit Info")
                edit_name = st.text_input("Name", value=selected_user_data[0], key=f"e_n_{selected_user_data[3]}")
                edit_reg = st.text_input("ID", value=selected_user_data[1], key=f"e_r_{selected_user_data[3]}")
                edit_course = st.text_input("Course", value=selected_user_data[4], key=f"e_c_{selected_user_data[3]}")
                
                if st.button("Save Changes", key=f"s_{selected_user_data[3]}", use_container_width=True):
                    if update_user_db(selected_user_data[3], selected_user_data[1], edit_name, edit_reg, edit_course):
                        st.success("Student details updated.")
                        st.rerun()
            
            with col2:
                st.write("#### 🗑️ Remove Student")
                st.warning("This will remove all photos and attendance history.")
                if st.button("Confirm Delete", type="primary", key=f"d_{selected_user_data[3]}", use_container_width=True):
                    if delete_user_db(selected_user_data[3], selected_user_data[1]):
                        shutil.rmtree(os.path.join("dataset", f"{selected_user_data[0]}_{selected_user_data[1]}"), ignore_errors=True)
                        encode_faces()
                        st.success("Student removed.")
                        st.rerun()
    else:
        st.info("No students registered yet.")
