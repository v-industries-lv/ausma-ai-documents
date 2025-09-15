import json
import shutil
import traceback
from abc import ABC, abstractmethod
from pathlib import Path
import os
from pypdf import PdfReader
from pdf2image import convert_from_path
from typing import List
from utils import compute_file_hash
from logger import logger

class DocumentFile(ABC):
    PDF_EXT = [".pdf"]
    TEXT_EXT = [".txt", ".md"]
    def __init__(self, doc_source_name: str, doc_source_root: str, file_path: str, document_type: str, needs_images: bool):
        self.doc_source_name: str = doc_source_name # DocSource.name
        self.doc_source_root: str = doc_source_root
        self.file_path: str = file_path # /path/to/file.ext
        self.document_type: str = document_type # "document", "email", etc

        self.file_name: str = Path(self.file_path).name
        self.extension: str = Path(self.file_name).suffix
        self.file_hash: str = self.calculate_hash()
        self.processed_path: str = str(
            os.path.join(
                "processed",
                self.get_output_path()
            )
        )
        self.needs_images = needs_images
        self.temp_image_path = os.path.join(os.getcwd(), "temp_images")

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

    @staticmethod
    def from_path(doc_source_name: str, doc_source_root: str, file_path: str):
        extension = Path(file_path).suffix
        if extension in DocumentFile.PDF_EXT:
            return PDFDocumentFile(doc_source_name, doc_source_root, file_path)
        if extension in DocumentFile.TEXT_EXT:
            return TextDocumentFile(doc_source_name, doc_source_root, file_path)
        return None

class PDFDocumentFile(DocumentFile):
    POPPLER_PATH = "/usr/bin"
    def __init__(self, doc_source_name: str, doc_source_root: str, file_path: str):
        super().__init__(doc_source_name, doc_source_root, file_path, document_type = "document", needs_images = True)

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
        self.clear_images()
        os.makedirs(self.temp_image_path, exist_ok=True)
        images = []
        logger.info(f"Creating temp images for {self.file_path}...")
        try:
            images = convert_from_path(
                pdf_path=self.file_path,
                dpi=300,
                poppler_path=PDFDocumentFile.POPPLER_PATH,
                output_folder=self.temp_image_path,
                paths_only=True,
                fmt="png",
            )
        except Exception as e:
            logger.error(f"Error processing document: {self.file_name}")
            logger.error(traceback.format_exc())

        return images

    def clear_images(self):
        if os.path.exists(self.temp_image_path):
            shutil.rmtree(self.temp_image_path)

class TextDocumentFile(DocumentFile):
    def __init__(self, doc_source_name: str, doc_source_root: str, file_path: str):
        super().__init__(doc_source_name, doc_source_root, file_path, document_type="document", needs_images=False)

    def raw_dump(self):
        logger.info(f"Raw dumping {self.file_path}")
        output_path = os.path.join(self.processed_path, "raw")
        os.makedirs(output_path, exist_ok=True)
        shutil.copy2(self.file_path, os.path.join(output_path, "1.txt"))