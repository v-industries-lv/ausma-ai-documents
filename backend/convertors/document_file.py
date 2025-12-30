import json
import shutil
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import os
from pypdf import PdfReader
from pdf_to_png import convert_pdf
from typing import List, Optional
from utils import compute_file_hash
from logger import logger

class DocumentFile(ABC):
    PDF_EXT = [".pdf"]
    TEXT_EXT = [".txt", ".md"]
    IMAGE_EXT = [".png", ".jpg", ".jpeg"]

    def __init__(self, doc_source_name: str, doc_source_root: str, file_path: str, document_type: str, image_based: bool,
                 precalc_file_hash: Optional[str] = None, last_modified: Optional[datetime] = None, file_size: int = -1):
        self.doc_source_name: str = doc_source_name # DocSource.name
        self.doc_source_root: str = doc_source_root
        self.file_path: str = file_path # /path/to/file.ext
        self.document_type: str = document_type # "document", "email", etc

        self.file_name: str = Path(self.file_path).name
        self.extension: str = Path(self.file_name).suffix
        self._file_hash: Optional[str] = precalc_file_hash
        self.processed_path: str = str(
            os.path.join(
                "processed",
                self.get_output_path()
            )
        )
        self.image_based = image_based
        self.temp_image_path = os.path.join(os.getcwd(), "temp_images")
        self.has_changed = False
        self.last_modified = last_modified
        self.file_size = file_size

    @property
    def file_hash(self) -> str:
        if self._file_hash is None:
            self._file_hash = self.calculate_hash()
        return self._file_hash

    def get_document_path(self):
        return os.path.join(self.doc_source_name, self.file_path)

    def calculate_hash(self) -> str:
        return compute_file_hash(self.file_path)

    def get_output_path(self):
        return os.path.relpath(
            self.file_path, self.doc_source_root
        ).replace(self.file_name, self.file_name + "_" + self.file_hash)

    def cleanup_output(self):
        if os.path.exists(self.processed_path):
            shutil.rmtree(self.processed_path)

    def _ensure_output_exists(self):
        os.makedirs(self.processed_path, exist_ok=True)

    def get_or_init_metadata(self) -> dict:
        if os.path.exists(os.path.join(self.processed_path, "metadata.json")):
            with open(os.path.join(self.processed_path, "metadata.json"), "r") as fh:
                loaded_metadata = json.load(fh)
                return loaded_metadata
        metadata = {
                    "type": self.document_type,
                    "filename": self.file_name,
                    "file_location": self.file_path,
                    "hash": self.file_hash,
                    "conversions": []
                }
        self._ensure_output_exists()
        metadata_path = os.path.join(self.processed_path, "metadata.json")
        temp_metadata_path = os.path.join(self.processed_path, "metadata.json.tmp")
        with open(temp_metadata_path, "w") as fh:
            json.dump(
                metadata,
                fh,
                indent=2
            )
        shutil.move(temp_metadata_path, metadata_path)
        return metadata

    def write_metadata(self, metadata):
        metadata_path = os.path.join(self.processed_path, "metadata.json")
        temp_metadata_path = os.path.join(self.processed_path, "metadata.json.tmp")
        with open(temp_metadata_path, "w") as fh:
            json.dump(
                metadata,
                fh,
                indent=2
            )
        shutil.move(temp_metadata_path, metadata_path)

    @abstractmethod
    def raw_dump(self):
        pass

    def cleanup_temp_files(self):
        # Override this for relevant DocumentFile's, by default does nothing.
        pass

    @staticmethod
    def create(doc_source_name: str, doc_source_root: str, file_path: str, precalc_file_hash: Optional[str] = None, last_modified: Optional[datetime] = None, file_size: int = -1):
        extension = Path(file_path).suffix.lower()
        if extension in DocumentFile.PDF_EXT:
            return PDFDocumentFile(doc_source_name, doc_source_root, file_path, precalc_file_hash, last_modified, file_size)
        if extension in DocumentFile.TEXT_EXT:
            return TextDocumentFile(doc_source_name, doc_source_root, file_path, precalc_file_hash, last_modified, file_size)
        if extension in DocumentFile.IMAGE_EXT:
            return ImageDocumentFile(doc_source_name, doc_source_root, file_path, precalc_file_hash, last_modified, file_size)
        return None

class ImageDocumentFile(DocumentFile):
    def raw_dump(self):
        raise(NotImplementedError(f"Trying to raw dump an image file. Not supported. {self.file_name}"))

    def __init__(self, doc_source_name: str, doc_source_root: str, file_path: str,
                 precalc_file_hash: Optional[str] = None, last_modified: Optional[datetime] = None, file_size: int = -1):
        super().__init__(doc_source_name, doc_source_root, file_path, document_type = "image", image_based = True,
                         precalc_file_hash = precalc_file_hash, last_modified =last_modified, file_size = file_size)

    def convert_document_to_images(self) -> List[str]:
        return [self.file_path]

class PDFDocumentFile(DocumentFile):
    POPPLER_PATH = "/usr/bin"
    def __init__(self, doc_source_name: str, doc_source_root: str, file_path: str,
                 precalc_file_hash: Optional[str] = None, last_modified: Optional[datetime] = None, file_size: int = -1):
        super().__init__(doc_source_name, doc_source_root, file_path, document_type = "document", image_based = True,
                         precalc_file_hash=precalc_file_hash, last_modified=last_modified, file_size=file_size)

    def raw_dump(self):
        logger.info(f"Raw dumping {self.file_path}")
        reader = PdfReader(self.file_path)
        conversion_output_path = os.path.join(self.processed_path, "raw")
        os.makedirs(conversion_output_path, exist_ok=True)
        for index, page in enumerate(reader.pages, 1):
            output_name = str(index).rjust(len(str(len(reader.pages))), "0") + ".txt"
            output_path = os.path.join(conversion_output_path, output_name)
            with open(output_path, "w") as fh:
                text = page.extract_text()
                fh.write(text)

    def convert_document_to_images(self) -> List[str]:
        self.cleanup_temp_files()
        os.makedirs(self.temp_image_path, exist_ok=True)
        images = []
        logger.info(f"Creating temp images for {self.file_path}...")
        try:
            images = convert_pdf(
                pdf_path=self.file_path,
                output_folder=self.temp_image_path,
            )
        except Exception as e:
            logger.error(f"Error processing document: {self.file_name}")
            logger.error(traceback.format_exc())

        return images

    def cleanup_temp_files(self):
        if os.path.exists(self.temp_image_path):
            shutil.rmtree(self.temp_image_path)

class TextDocumentFile(DocumentFile):
    def __init__(self, doc_source_name: str, doc_source_root: str, file_path: str,
                 precalc_file_hash: Optional[str] = None, last_modified: Optional[datetime] = None, file_size: int = -1):
        super().__init__(doc_source_name, doc_source_root, file_path, document_type="document", image_based=False,
                         precalc_file_hash=precalc_file_hash, last_modified=last_modified, file_size=file_size)

    def raw_dump(self):
        logger.info(f"Raw dumping {self.file_path}")
        output_path = os.path.join(self.processed_path, "raw")
        os.makedirs(output_path, exist_ok=True)
        shutil.copy2(self.file_path, os.path.join(output_path, "1.txt"))