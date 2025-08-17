import os
import shutil
from typing import List, Tuple, Optional
from venv import logger
from tqdm import tqdm
from PyPDF2 import PdfReader

locations: List[Tuple[str, str]] = [
    ("Location: Cambridge", "Cambridge"),
    ("Location: Cambridge  – Maddingley Road", "CambridgeMaddingleyRoad"),
    ("Location: Cambridge  – Science Park", "CambridgeSciencePark"),
    ("Your normal place of work will be Cambridge .", "Cambridge"),
    ("Your normal place of work will be Cambridge  – Maddingley Road .", "CambridgeMaddingleyRoad"),
    ("Your normal place of work will be Cambridge  – Science Park .", "CambridgeSciencePark"),
]
default_folder: str = "Other"

important_text: List[str] = [
    "Cambridge",
    "Place of work",
    "Maddingley Road",
    "Science Park",
]

pdf_folder: str = "originalPDFs"
output_base: str = "pdf_outputs"

def find_location(text: str, locations: List[Tuple[str, str]]) -> Optional[str]:
    sorted_locations: List[Tuple[str, str]] = sorted(locations, key=lambda x: len(x[0]), reverse=True)
    lines: List[str] = [line.rstrip() for line in text.splitlines()]
    for search, folder in sorted_locations:
        if any(line.endswith(search) for line in lines):
            return folder
    return None

def find_important_lines(text: str, important_text: List[str]) -> List[str]:
    lines: List[str] = [line.rstrip() for line in text.splitlines()]
    important_lines: List[str] = []
    previous_line: Optional[str] = None
    last_important_line_index: Optional[int] = None
    for line_index, line in enumerate(lines):
        last_line_was_important: bool = (
                last_important_line_index is not None
                and
                line_index == last_important_line_index + 1
            )
        current_line_is_important: bool = any(important in line for important in important_text)
        if current_line_is_important:
            if not last_line_was_important and previous_line:
                important_lines.append(previous_line)
            important_lines.append(line)
            last_important_line_index = line_index
        elif last_line_was_important:
            important_lines.append(line)
        previous_line = line
    return important_lines

def process_pdf_file(filename: str, pdf_folder: str, output_base: str, locations: List[Tuple[str, str]], default_folder: str) -> None:
    if filename.lower().endswith(".pdf"):
        pdf_path: str = os.path.join(pdf_folder, filename)
        try:
            reader: PdfReader = PdfReader(pdf_path)
            text: str = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            folder_name: Optional[str] = find_location(text, locations)
            important_lines: List[str] = find_important_lines(text, important_text)
            if folder_name:
                dest_folder: str = os.path.join(output_base, folder_name)
            else:
                dest_folder = os.path.join(output_base, default_folder)
            os.makedirs(dest_folder, exist_ok=True)
            shutil.copy2(pdf_path, dest_folder)
            with open(os.path.join(dest_folder, f"{filename}_important.txt"), "w") as f:
                f.write("\n".join(important_lines))
            logger.info(f"Copied {filename} to {dest_folder}")
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

def main() -> None:
    if not os.path.exists(output_base):
        os.makedirs(output_base)
    files = os.listdir(pdf_folder)
    for filename in tqdm(files, desc="Processing PDFs", unit="file"):
        process_pdf_file(filename, pdf_folder, output_base, locations, default_folder)

if __name__ == "__main__":
    main()
