import dlib
import numpy as np
import face_recognition_models
import streamlit as st

from src.database.db import get_all_students

@st.cache_resource
def load_dlib_models(): 
    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(face_recognition_models.pose_predictor_model_location())

    facerec = dlib.face_recognition_model_v1(face_recognition_models.face_recognition_model_location())

    return detector, sp, facerec

def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_models()

    faces = detector(image_np, 1)

    encodings = []
    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1) #128 embedding

        encodings.append(np.array(face_descriptor))
    return encodings

def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)
    detected_student = {}
    students = get_all_students()
    candidates = []

    for student in students:
        embedding = student.get('face_embedding')
        if embedding is None:
            continue

        student_embedding = np.asarray(embedding, dtype=float)
        if student_embedding.shape == (128,) and np.isfinite(student_embedding).all():
            candidates.append((student['student_id'], student_embedding))

    for encoding in encodings:
        best_match_id = None
        best_match_score = float('inf')

        for student_id, student_embedding in candidates:
            score = np.linalg.norm(student_embedding - encoding)
            if score < best_match_score:
                best_match_id = student_id
                best_match_score = score

        if best_match_id is not None and best_match_score <= 0.6:
            detected_student[best_match_id] = True

    return detected_student, [student_id for student_id, _ in candidates], len(encodings)