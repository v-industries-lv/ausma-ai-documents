import argparse
import os
import re
import traceback
from pdf2image import convert_from_path
from pypdf import PdfReader

from convertors import ocr_convertor, ocr_with_llm_convertor, llm_convertor


def pdf_to_image(input_file_path, output_path, poppler_path, dpi: int = 300):
    pages = convert_from_path(input_file_path, dpi=dpi, poppler_path=poppler_path)
    pages_str = str(len(pages)).rjust(len(str(len(pages))), "0")
    for count, page in enumerate(pages):
        page_id = str(count).rjust(len(str(len(pages))), "0")
        print(page_id, "of", pages_str)

        page.save(os.path.join(output_path, page_id+".jpg"), 'JPEG', single_file=True)
    del pages

def image_to_text(convertor, image_files, input_root, document, document_images_output):
    print("Doing", convertor.convertor_type)
    image_to_text_output_path = os.path.join(input_root, "text", convertor.convertor_type, document)
    os.makedirs(image_to_text_output_path, exist_ok=True)
    for image_file in image_files:
        print(convertor.convertor_type, image_file)
        image_path = os.path.join(document_images_output, image_file)
        with open(os.path.join(image_to_text_output_path, image_file.replace(".jpg", ".txt")), "w") as fh:
            fh.write(convertor.image_to_text(image_path))

def main(args):
    conversions = args.conversions.split(';')

    if 'ocr_llm' in conversions:
        if args.text_model:
            text_model = args.text_model
        else:
            raise(ValueError('Missing text model for ocr_llm convertor'))
    if 'llm' in conversions:
        if args.vision_model:
            vision_model = args.vision_model
        else:
            raise (ValueError('Missing vision model for llm convertor'))

    input_root = args.input_root if args.input_root is not None else ''
    documents_folder = os.path.join(input_root, "documents")

    for document in os.listdir(documents_folder):
        print(document)
        document_path = os.path.join(documents_folder, document)
        if document.endswith(".pdf"):
            # RAW convert
            if 'raw' in conversions:
                print("Raw dumping", document)
                reader = PdfReader(document_path)
                os.makedirs(os.path.join(input_root, "text", "raw", document), exist_ok=True)
                for index, page in enumerate(reader.pages):
                    output_name = "page_" + str(index).rjust(len(str(len(reader.pages))), "0") + ".txt"
                    with open(os.path.join(input_root, "text", "raw", document, output_name), "w") as fh:
                        text = page.extract_text()
                        text = text.replace('\xa0\n', '')
                        pattern = r"([a-zA-Z0-9,’])(\s\n)([a-zA-Z0-9])"
                        text = re.sub(pattern, r"\1 \3", text)
                        pattern = r"([a-zA-Z0-9])([—])(\n)([a-zA-Z0-9])"
                        text = re.sub(pattern, r"\1 \2 \4", text)
                        fh.write(text)
            if len([x for x in ['ocr', 'ocr_llm', 'llm'] if x in conversions]) > 0:
                # Document to images
                dpi = args.dpi if args.dpi else 300
                document_images_path = os.path.join(input_root, "images")
                document_images_output = os.path.join(document_images_path, document)
                os.makedirs(document_images_output, exist_ok=True)
                try:
                    pdf_to_image(
                        input_file_path=document_path,
                        output_path=document_images_output,
                        poppler_path=args.poppler_path,
                        dpi=dpi,
                    )
                except Exception as e:
                    print(f"Error processing document: {document}")
                    print(traceback.format_exc())
                image_files = os.listdir(document_images_output)
                if len(image_files) > 0:
                    image_files.sort()
                    # Image to text: OCR
                    if 'ocr' in conversions:
                        image_to_text(
                            convertor=ocr_convertor.OCR_convertor(),
                            image_files=image_files,
                            input_root=input_root,
                            document=document,
                            document_images_output=document_images_output
                        )

                    # Image to text: OCR + LLM
                    if 'ocr_llm' in conversions:
                        image_to_text(
                            convertor=ocr_with_llm_convertor.OCR_LLM_convertor(model=text_model),
                            image_files=image_files,
                            input_root=input_root,
                            document=document,
                            document_images_output=document_images_output
                        )

                    # Image to text: LLM
                    if 'llm' in conversions:
                        image_to_text(
                            convertor=llm_convertor.LLM_convertor(model=vision_model),
                            image_files=image_files,
                            input_root=input_root,
                            document=document,
                            document_images_output=document_images_output
                        )
        else:
            print(f"Cannot process document {document}. Filetype not supported")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--poppler-path", help="Path to poppler.", type=str, default="/usr/bin/")
    parser.add_argument("--input-root", help="Input document root", type=str)
    parser.add_argument("--text-model", help="Model used for text cleanup", type=str)
    parser.add_argument("--vision-model", help="Model used for text recognition", type=str)
    parser.add_argument("--conversions", help="Conversions separated by ';'. Conversions available: raw, ocr, ocr_llm, llm", type=str, required=True)
    parser.add_argument("--dpi", help="Image dpi.", type=int)

    args = parser.parse_args()

    main(args)