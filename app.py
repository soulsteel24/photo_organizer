from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import os
import face_recognition
import json

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

# Encode faces and cache results
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
                encoding = face_recognition.face_encodings(image)
                if encoding:
                    known_encodings[name] = encoding[0].tolist()
            known_face_encodings.append(known_encodings[name])
            known_face_names.append(name)

    save_encodings(known_encodings)
    return known_face_encodings, known_face_names

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
        known_face_encodings, known_face_names = encode_faces()
        image_paths = []

        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
            for file in files:
                if file.endswith('.jpg') or file.endswith('.png'):
                    image_path = os.path.join(root, file)
                    image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(image)
                    
                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                        if any(matches):
                            name = known_face_names[matches.index(True)]
                            if user_query.lower() in name.lower():
                                image_paths.append(image_path)
                                break
        
        images = [{'filename': os.path.basename(path)} for path in image_paths]
        return render_template('search.html', images=images)
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
