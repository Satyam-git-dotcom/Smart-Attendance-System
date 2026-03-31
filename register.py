import cv2
import os
import time

def register_user(name, reg_no):
    """
    Captures 20 images of a new user from the webcam for training.
    Folders are named 'Name_RegNo' for unique identification.
    """
    # Create identification string
    identity = f"{name}_{reg_no}"
    save_path = os.path.join("dataset", identity)
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    else:
        print(f"User with ID {reg_no} already exists. Overwriting dataset...")

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Error: Could not open webcam.")
        return False

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    count = 0
    print(f"Starting registration for {name} (ID: {reg_no}).")
    print("Please look at the camera and move your head slowly to capture different angles.")
    
    while count < 20:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            face_img = frame[y:y+h, x:x+w]
            img_name = f"{save_path}/{identity}_{count}.jpg"
            cv2.imwrite(img_name, face_img)
            
            # Draw rectangle for feedback
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, f"Captured: {count}/20", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            
            # Slow down capture to get different angles
            time.sleep(0.5)

        cv2.imshow("Registering User - Press Q to Quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    print(f"Data collection complete for {name}.")
    return True

if __name__ == "__main__":
    from src.recognize import encode_faces
    from src.attendance import register_user_db, init_db

    print("--- User Registration ---")
    name = input("Enter Name: ").strip()
    reg_no = input("Enter Registration Number: ").strip()
    
    if name and reg_no:
        if register_user(name, reg_no):
            init_db()
            identity = f"{name}_{reg_no}"
            if register_user_db(name, reg_no):
                print("Generating face encodings (this may take a moment)...")
                encode_faces()
                print(f"User {name} (ID: {reg_no}) registered successfully!")
            else:
                print(f"Error: Registration Number {reg_no} is already taken.")
    else:
        print("Error: Name and Registration Number are required.")
