from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import zipfile
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import certifi
import datetime

# Setup Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MongoDB Atlas connection
MONGO_URI = MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["user_files"]
collection = db["uploads"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    username = request.form['username']
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        username_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        os.makedirs(username_folder, exist_ok=True)
        zip_path = os.path.join(username_folder, secure_filename(file.filename))
        file.save(zip_path)

        # Extract files from zip and flatten the structure
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            index_found = False
            for member in zip_ref.namelist():
                if member.endswith('/'):
                    continue
                if os.path.basename(member).lower() == "index.html":
                    index_found = True
                source = zip_ref.open(member)
                target_path = os.path.join(username_folder, os.path.basename(member))
                if not os.path.exists(target_path):
                    with open(target_path, "wb") as target:
                        target.write(source.read())

        os.remove(zip_path)

        if not index_found:
            return "Error: index.html not found in zip!"

        # Store metadata in MongoDB
        upload_info = {
            "username": username,
            "filename": file.filename,
            "uploaded_at": datetime.datetime.utcnow(),
            "filetype": "zip",
            "contains_index": index_found
        }
        collection.insert_one(upload_info)

        return redirect(url_for('user_site', username=username))

@app.route('/<username>/')
def user_site(username):
    user_path = os.path.join(app.config['UPLOAD_FOLDER'], username)
    return send_from_directory(user_path, 'index.html')

@app.route('/<username>/<path:filename>')
def serve_user_files(username, filename):
    user_path = os.path.join(app.config['UPLOAD_FOLDER'], username)
    return send_from_directory(user_path, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
