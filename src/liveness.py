import numpy as np
from scipy.spatial import distance as dist

def calculate_ear(eye):
    """
    Calculate the Eye Aspect Ratio (EAR) for liveness (blink) detection.
    """
    # Compute the euclidean distances between the two sets of
    # vertical eye landmarks (x, y)-coordinates
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # Compute the euclidean distance between the horizontal
    # eye landmark (x, y)-coordinates
    C = dist.euclidean(eye[0], eye[3])

    # Compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)

    return ear

def check_liveness(shape, left_eye_indices, right_eye_indices, ear_threshold=0.25):
    """
    Check if the person is blinking based on facial landmarks.
    """
    # Extract eye coordinates
    left_eye = shape[left_eye_indices]
    right_eye = shape[right_eye_indices]

    # Calculate EAR for both eyes
    left_ear = calculate_ear(left_eye)
    right_ear = calculate_ear(right_eye)

    # Average the EAR
    avg_ear = (left_ear + right_ear) / 2.0

    return avg_ear < ear_threshold, avg_ear
