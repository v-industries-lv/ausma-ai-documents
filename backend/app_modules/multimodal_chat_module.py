import json
from typing import List
import hashlib
import os
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from flask import request, Flask, send_from_directory
from logger import logger
from utils import resize_image_with_limits
from globals import PROJECT_DATA_PATH

class MMChatModule:
    SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]
    UPLOAD_FOLDER = os.path.join(PROJECT_DATA_PATH, "instance", "blobs", "multimodal_input")

    class UploadedFile:
        def __init__(self, file_storage: FileStorage):
            self._file_storage = file_storage
            self.filename = secure_filename(self._file_storage.filename)
            self.hash = None
            self._set_hash()
            self.path = None
            self.new_filename = None
            self.ext = None
            self._set_path_and_ext()

        def _set_hash(self):
            hasher = hashlib.sha256()
            for chunk in iter(lambda: self._file_storage.stream.read(4096), b""):
                hasher.update(chunk)
            self.hash = hasher.hexdigest()
            self._file_storage.stream.seek(0)

        def _set_path_and_ext(self):
            _, ext = os.path.splitext(self.filename)
            new_filename = f"{self.hash}{ext}"
            output_path = os.path.join(MMChatModule.UPLOAD_FOLDER, new_filename)
            self.path = output_path
            self.new_filename = new_filename
            self.ext = ext

        def _is_file_too_large(self):
            stream = self._file_storage.stream
            stream.seek(0, 2)
            size = stream.tell()
            stream.seek(0)

            # Files over 20 MB are too large
            return size > 20 * 1024 * 1024

        def _is_image_not_valid(self):
            MAX_SIDE = 2000
            stream = self._file_storage.stream
            try:
                img = Image.open(stream)
            except Exception as e:
                stream.seek(0)
                logger.error(f"Failed to parse image {self.filename}! Error: {e}")
                return True
            stream.seek(0)
            w, h = img.size
            # Try to prevent "image bombs"
            return w >= MAX_SIDE * 100 or h >= MAX_SIDE * 100


        def validate(self):
            if self.ext not in MMChatModule.SUPPORTED_IMAGE_EXTENSIONS:
                raise(ValueError(f"Extension {self.ext} not supported! Supported: {MMChatModule.SUPPORTED_IMAGE_EXTENSIONS}"))
            if self._is_file_too_large():
                raise(ValueError(f"File {self.filename} too large!"))
            if self._is_image_not_valid():
                raise(ValueError(f"Image {self.filename} not valid!"))

        def save(self):
            self.validate()
            os.makedirs(MMChatModule.UPLOAD_FOLDER, exist_ok=True)
            if os.path.exists(self.path):
                return
            stream = self._file_storage.stream
            img = Image.open(stream)
            img = resize_image_with_limits(img).convert("RGB")
            img.save(self.path)

        def to_dict(self):
            return {
                "original_clean_filename": self.filename,
                "new_filename": self.new_filename,
                "path": self.path,
            }

    def __init__(self):
        pass

    @staticmethod
    def apply_routes(app: Flask, base_path=''):
        @app.errorhandler(RequestEntityTooLarge)
        def handle_file_too_large(e):
            return {"error": "Uploaded files too large"}, 413

        @app.route("/instance/blobs/multimodal_input/<filename>")
        def uploaded_file(filename):
            return send_from_directory(os.path.join(base_path, MMChatModule.UPLOAD_FOLDER), filename)

        @app.route("/api/upload_chat_files", methods=["POST"])
        def upload_chat_files():
            if "files" not in request.files:
                return app.response_class(
                    response=json.dumps({"error": "No files in request"}, indent=2),
                    mimetype='application/json'
                )

            files: List[FileStorage] = request.files.getlist("files")
            paths = []
            errors = []
            for file in files:
                uploaded_file = MMChatModule.UploadedFile(file)
                try:
                    uploaded_file.save()
                    paths.append(uploaded_file.to_dict())
                except Exception as e:
                    err = f"Failed to validate {uploaded_file.filename}. Error: {e}"
                    logger.error(err)
                    errors.append(err)
            return app.response_class(
                response=json.dumps({"files": paths, "errors": errors}, indent=2),
                mimetype='application/json'
            )