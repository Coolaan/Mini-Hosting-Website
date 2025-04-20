from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
import zipfile

# MongoDB related imports
import pymongo
import certifi

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize USE_MONGO to False by default
USE_MONGO = False
MONGO_URI = ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global USE_MONGO
    global MONGO_URI
    
    username = request.form['username']
    use_mongo = request.form.get('use_mongo')  # Check if MongoDB is selected
    
    # Set USE_MONGO flag based on the form submission
    if use_mongo == 'true':
        USE_MONGO = True
        MONGO_URI = os.environ.get("MONGO_URI")  # Get the Mongo URI from environment variable
    else:
        USE_MONGO = False
    
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    
    if file:
        # Create a folder for the user (username)
        username_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        os.makedirs(username_folder, exist_ok=True)
        zip_path = os.path.join(username_folder, secure_filename(file.filename))
        file.save(zip_path)

        # Extract files from the zip and store them in the user's folder
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            index_found = False
            for member in zip_ref.namelist():
                # Check if it's a directory, skip it
                if member.endswith('/'):
                    continue

                # Look for index.html (if you are hosting a website)
                if os.path.basename(member).lower() == "index.html":
                    index_found = True

                # Extract the file to the user folder
                source = zip_ref.open(member)
                target_path = os.path.join(username_folder, os.path.basename(member))

                if not os.path.exists(target_path):
                    with open(target_path, "wb") as target:
                        target.write(source.read())

        # Remove the uploaded zip file
        os.remove(zip_path)

        # If MongoDB is used, store information about the file
        if USE_MONGO:
            client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            db = client['file_db']  # Database name
            collection = db['files']  # Collection name
            file_info = {
                "username": username,
                "filename": file.filename,
                "path": zip_path
            }
            collection.insert_one(file_info)

        if not index_found:
            return "Error: index.html not found in zip!"

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
    # Ensure the upload folder is created if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Get the port from environment variables (for Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

