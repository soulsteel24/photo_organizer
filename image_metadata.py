import os
import re
from app import db, Image, app

def store_image_metadata(image_folder):
    with app.app_context():
        for filename in os.listdir(image_folder):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                keywords = re.sub(r'[_.-]', ' ', filename).split()
                image = Image(filename=filename, keywords=' '.join(keywords))
                db.session.add(image)
        db.session.commit()

if __name__ == "__main__":
    store_image_metadata(r'C:\Users\Legion\OneDrive\Desktop\python_work\converted')
