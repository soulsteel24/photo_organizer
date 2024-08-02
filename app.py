from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import os
import face_recognition
import json
from PIL import Image
import concurrent.futures

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'C:/Users/Legion/OneDrive/Desktop/python_work/converted'
app.config['KNOWN_FACES_FOLDER'] = 'C:/Users/Legion/OneDrive/Desktop/python_work/known_faces'
app.config['ENCODINGS_FILE'] = 'C:/Users/Legion/OneDrive/Desktop/python_work/known_faces/encodings.json'

if not os.path.exists(app.config['KNOWN_FACES_FOLDER']):
    os.makedirs(app.config['KNOWN_FACES_FOLDER'])

# Function to load cached encodings
def load_encodings():
    if os.path.exists(app.config['ENCODINGS_FILE']):
        with open(app.config['ENCODINGS_FILE'], 'r') as f:
            return json.load(f)
    return {}

# Function to save encodings to cache
def save_encodings(encodings):
    with open(app.config['ENCODINGS_FILE'], 'w') as f:
        json.dump(encodings, f)

# Function to encode faces and cache results
def encode_faces():
    known_encodings = load_encodings()
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(app.config['KNOWN_FACES_FOLDER']):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            name = filename.split('.')[0]
            if name not in known_encodings:
                image_path = os.path.join(app.config['KNOWN_FACES_FOLDER'], filename)
                image = face_recognition.load_image_file(image_path)
                encoding = face_recognition.face_encodings(image, num_jitters=10)
                if encoding:
                    known_encodings[name] = encoding[0].tolist()
            known_face_encodings.append(known_encodings[name])
            known_face_names.append(name)

    save_encodings(known_encodings)
    return known_face_encodings, known_face_names

# Function to resize images
def resize_image(image_path, max_size=(800, 800)):
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        img.save(image_path)

# Function to align faces using landmarks
def align_face(image):
    face_landmarks_list = face_recognition.face_landmarks(image)
    if face_landmarks_list:
        for face_landmarks in face_landmarks_list:
            # Example alignment logic (details omitted)
            pass
    return image

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_people', methods=['GET', 'POST'])
def add_people():
    if request.method == 'POST':
        names = request.form.getlist('name')
        images = request.files.getlist('image')
        
        for name, image in zip(names, images):
            if name and image:
                image_path = os.path.join(app.config['KNOWN_FACES_FOLDER'], f'{name}.jpg')
                image.save(image_path)
                resize_image(image_path)  # Resize image for optimization
        return redirect(url_for('add_people'))
    
    known_face_names = [f.split('.')[0] for f in os.listdir(app.config['KNOWN_FACES_FOLDER']) if f.endswith('.jpg') or f.endswith('.png')]
    return render_template('add_people.html', known_face_names=known_face_names)

@app.route('/remove_person/<name>')
def remove_person(name):
    image_path = os.path.join(app.config['KNOWN_FACES_FOLDER'], f'{name}.jpg')
    if os.path.exists(image_path):
        os.remove(image_path)
    return redirect(url_for('add_people'))

@app.route('/search', methods=['POST'])
def search():
    user_query = request.form.get('userQuery')
    if user_query:
        search_names = [name.strip() for name in user_query.split(',')]
        known_face_encodings, known_face_names = encode_faces()
        image_paths = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
                for file in files:
                    if file.endswith('.jpg') or file.endswith('.png'):
                        image_path = os.path.join(root, file)
                        futures.append(executor.submit(process_image, image_path, known_face_encodings, known_face_names, search_names))

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    image_paths.append(result)

        images = [{'filename': os.path.basename(path)} for path in image_paths]
        return render_template('search.html', images=images)
    return redirect(url_for('index'))

def process_image(image_path, known_face_encodings, known_face_names, search_names):
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)

    found_names = set()
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
        for match, name in zip(matches, known_face_names):
            if match:
                found_names.add(name)
    if all(name in found_names for name in search_names):
        return image_path
    return None

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
