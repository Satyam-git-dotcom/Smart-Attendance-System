import face_recognition
import numpy as np
import cv2
import os
import pickle

ENCODINGS_PATH = "encodings/encodings.pickle"
DATASET_PATH = "dataset"

def load_encodings():
    """
    Loads saved face encodings from a pickle file.
    """
    if os.path.exists(ENCODINGS_PATH):
        with open(ENCODINGS_PATH, "rb") as f:
            data = pickle.load(f)
        return data
    return {"encodings": [], "names": []}

def save_encodings(encodings, names):
    """
    Saves face encodings to a pickle file.
    """
    os.makedirs(os.path.dirname(ENCODINGS_PATH), exist_ok=True)
    data = {"encodings": encodings, "names": names}
    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump(data, f)

def encode_faces():
    """
    Processes all images in the dataset and generates face encodings.
    """
    known_encodings = []
    known_names = []

    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset path '{DATASET_PATH}' does not exist.")
        return 0

    # Iterate through user folders in dataset
    for person_name in os.listdir(DATASET_PATH):
        person_dir = os.path.join(DATASET_PATH, person_name)
        if not os.path.isdir(person_dir):
            continue

        for image_name in os.listdir(person_dir):
            image_path = os.path.join(person_dir, image_name)
            image = face_recognition.load_image_file(image_path)
            
            # Identify face locations and encodings
            encodings = face_recognition.face_encodings(image)
            
            for encoding in encodings:
                known_encodings.append(encoding)
                known_names.append(person_name)

    save_encodings(known_encodings, known_names)
    return len(known_names)

def recognize_face(frame, known_data, tolerance=0.5):
    """
    Recognizes faces in a given video frame.
    Returns the names and locations of detected faces.
    """
    if frame is None or frame.size == 0:
        return [], []

    # Resize frame to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert frame to RGB (face_recognition uses RGB)
    # Using cv2.cvtColor instead of slicing [:, :, ::-1] ensures the array is C-contiguous
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Find face locations and encodings in the small frame
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []
    for face_encoding in face_encodings:
        # Check for matches
        matches = face_recognition.compare_faces(known_data["encodings"], face_encoding, tolerance=tolerance)
        name = "Unknown"

        # Calculate distances to find the best match
        face_distances = face_recognition.face_distance(known_data["encodings"], face_encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_data["names"][best_match_index]

        face_names.append(name)

    # Scale back up face locations since the frame we detected in was scaled to 1/4 size
    # Face locations are (top, right, bottom, left)
    face_locations = [(top * 4, right * 4, bottom * 4, left * 4) for (top, right, bottom, left) in face_locations]

    return face_locations, face_names
