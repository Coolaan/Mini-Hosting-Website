from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

        # Extract all files while flattening folder structure
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            index_found = False
            for member in zip_ref.namelist():
                # Check if it's a directory, skip directories
                if member.endswith('/'):
                    continue  # Skip directories

                # Check if index.html exists anywhere
                if os.path.basename(member).lower() == "index.html":
                    index_found = True

                # Extract file to user folder
                source = zip_ref.open(member)
                target_path = os.path.join(username_folder, os.path.basename(member))

                # Ensure the target is a file, not a directory
                if not os.path.exists(target_path):
                    with open(target_path, "wb") as target:
                        target.write(source.read())

        os.remove(zip_path)

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
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', port=port, debug=True)

