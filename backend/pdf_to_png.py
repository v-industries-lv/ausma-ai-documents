import os
import shutil
import subprocess
import uuid
from typing import List, Optional
from pdf2image import convert_from_path

from logger import logger


def make_absolute_path(path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.abspath(os.path.join(os.getcwd(), path))


def convert_pdf(pdf_path: str, output_folder: str = "temp_images") -> Optional[List[str]]:
    pdf_path = make_absolute_path(pdf_path)
    temp_folder = os.path.join(os.getcwd(), output_folder)
    paths = None
    if not get_xpdf_path() == "__disabled__":
        try:
            paths = xpdf_convert(pdf_path, temp_folder)
        except Exception as e:
            logger.error(f"XPDF could not convert pdf. Error: {e}")
    if paths is None and not get_poppler_path() == "__disabled__":
        try:
            paths = poppler_convert(pdf_path, temp_folder)
        except Exception as e:
            logger.error(f"POPPLER could not convert pdf. Error: {e}")
    if paths is None:
        logger.error(f"Could not convert pdf to images! File: {pdf_path}")
    return paths


def xpdf_convert(pdf_path: str, output: str) -> List[str]:
    """
    OPTIONS:
    −f number - Specifies the first page to convert.
    −l number - Specifies the last page to convert.
    −r number - Specifies the resolution, in DPI. The default is 150 DPI.
    −mono - Generate a monochrome image (instead of a color image).
    −gray - Generate a grayscale image (instead of a color image).
    −alpha - Generate an alpha channel in the PNG file. This is only useful with PDF files that have been constructed with a transparent background. The −alpha flag cannot be used with −mono.
    −rot - angle Rotate pages by 0 (the default), 90, 180, or 270 degrees.
    −freetype yes | no - Enable or disable FreeType (a TrueType / Type 1 font rasterizer). This defaults to "yes". [config file: enableFreeType]
    −aa yes | no - Enable or disable font anti-aliasing. This defaults to "yes". [config file: antialias]
    −aaVector yes | no - Enable or disable vector anti-aliasing. This defaults to "yes". [config file: vectorAntialias]
    −opw password - Specify the owner password for the PDF file. Providing this will bypass all security restrictions.
    −upw password - Specify the user password for the PDF file.
    −verbose - Print a status message (to stdout) before processing each page. [config file: printStatusInfo]
    −q - Don’t print any messages or errors. [config file: errQuiet]
    −cfg - config-file Read config-file in place of ~/.xpdfrc or the system-wide config file.
    −v - Print copyright and version information.
    −h - Print usage information. (−help and −−help are equivalent.)
    """
    xpdf_path = get_xpdf_path()

    prefix = str(uuid.uuid4())
    if os.path.exists(output):
        shutil.rmtree(output)
    os.makedirs(output, exist_ok=True)

    args = ["-r", "300"]
    subprocess.run(
        [xpdf_path] + args + [pdf_path, prefix],
        cwd=output,
        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
    )

    return sorted([os.path.join(output, x) for x in os.listdir(output)])


def get_xpdf_path() -> str:
    return make_absolute_path(os.environ.get("XPDF_PATH", os.path.join(os.getcwd(), "bin", "linux", "pdftopng")))

def get_poppler_path() -> str:
    return make_absolute_path(os.environ.get("POPPLER_PATH", "/usr/bin"))

def poppler_convert(pdf_path: str, output: str) -> List[str]:
    # Library telling lies about output type. If paths_only=True, then List[str], not List[Image]
    # noinspection PyTypeChecker
    images: List[str] = convert_from_path(
        pdf_path=pdf_path,
        dpi=300,
        poppler_path=get_poppler_path(),
        output_folder=output,
        paths_only=True,
        fmt="png",
    )
    return images
