import sqlite3
import face_recognition
import numpy as np
import cv2
import os

# Directory containing the images
image_directory = r'C:\Users\Legion\OneDrive\Desktop\python_work\converted'

# Connect to SQLite database (or create it)
conn = sqlite3.connect('face_recognition.db')
c = conn.cursor()

# Create table to store face encodings
c.execute('''CREATE TABLE IF NOT EXISTS faces
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              encoding BLOB)''')
conn.commit()

def store_face(name, image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    
    if encodings:
        encoding = encodings[0]
        encoding_blob = sqlite3.Binary(np.array(encoding).tobytes())
        
        c.execute("INSERT INTO faces (name, encoding) VALUES (?, ?)", (name, encoding_blob))
        conn.commit()
        print(f"Stored {name} encoding.")
    else:
        print(f"No face found in {image_path}.")

def retrieve_faces():
    c.execute("SELECT name, encoding FROM faces")
    rows = c.fetchall()
    faces = []
    for row in rows:
        name = row[0]
        encoding = np.frombuffer(row[1], dtype=np.float64)
        faces.append((name, encoding))
    return faces

def recognize_face(image_path, threshold=0.5):
    unknown_image = face_recognition.load_image_file(image_path)
    unknown_image_encodings = face_recognition.face_encodings(unknown_image)
    
    faces = retrieve_faces()
    
    for unknown_image_encoding in unknown_image_encodings:
        for name, known_encoding in faces:
            face_distance = face_recognition.face_distance([known_encoding], unknown_image_encoding)[0]
            is_match = face_distance < threshold
            
            if is_match:
                print(f"Match found: {name} (Distance: {face_distance})")
                return name
            else:
                print(f"No match for {name} (Distance: {face_distance})")
    return None

# Store known faces from the directory
for filename in os.listdir(image_directory):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        name = os.path.splitext(filename)[0]  # Use the filename without extension as the name
        image_path = os.path.join(image_directory, filename)
        store_face(name, image_path)

# Recognize face in an unknown image (example)
unknown_image_path = 'unknown_person.jpg'
recognized_name = recognize_face(unknown_image_path)
if recognized_name:
    print(f"Recognized: {recognized_name}")
else:
    print("No match found")

# Close the database connection
conn.close()
