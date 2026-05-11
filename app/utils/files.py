import os
import random
import string
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{random_string(10)}_{filename}"

        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            current_app.logger.error('UPLOAD_FOLDER is not configured.')
            return None

        try:
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, unique_filename)
            file.save(filepath)
            return f'uploads/{unique_filename}'
        except Exception as e:
            current_app.logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
            return None

    return None

def random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
