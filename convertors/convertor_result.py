from typing import List, Optional

class ConvertorResult:
    def __init__(self, pages: List[str], document_metadata: dict, conversion_type: str, model: Optional[str], output_folder_name: str, output_path: str, result_hash: Optional[str]):
        self.pages = pages
        # Metadata contains specific document metadata.
        self.document_metadata = document_metadata
        self.output_folder_name = output_folder_name
        self.conversion_type = conversion_type
        self.model = model
        self.output_path = output_path
        self.result_hash = result_hash