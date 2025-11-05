import os
import shutil
import subprocess
import uuid
from typing import List


def make_absolute_path(path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.abspath(os.path.join(os.getcwd(), path))


def convert_from_path(pdf_path: str, xpdf_path: str, output_folder: str = "temp_images") -> List[str]:
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

    pdf_path = make_absolute_path(pdf_path)
    xpdf_path = make_absolute_path(xpdf_path)

    prefix = str(uuid.uuid4())
    temp_folder = os.path.join(os.getcwd(), output_folder)
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    os.makedirs(temp_folder, exist_ok=True)

    args = ["-r", "300"]
    subprocess.run(
        [xpdf_path] + args + [pdf_path, prefix],
        cwd=temp_folder,
        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
    )

    return sorted([os.path.join(temp_folder, x) for x in os.listdir(temp_folder)])

