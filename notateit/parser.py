__author__ = 'Nikita Denissov'

import re
import struct
import zlib
from pathlib import Path
from typing import Any

HEADER_LENGTH = 13
PAGE_BREAK_REGEX = re.compile(b'\xff\xff\xff\xff\x00\x00\x00\x00', re.DOTALL)
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
ZLIB_HEADER = b'x\x9c'
TEXT_REGEX = re.compile(b'(.{4})([^<\0]+)<\0')


def parse_page_simple(page_data: bytes, page_num: int, assets_dir: Path) -> list[dict[str, Any]]:
    objects = []
    cursor = 0
    img_index = 0

    while cursor < len(page_data):
        text_match = TEXT_REGEX.search(page_data, cursor)
        png_pos = page_data.find(PNG_SIGNATURE, cursor)

        next_text_pos = text_match.start() if text_match else -1
        next_png_pos = png_pos if png_pos != -1 else -1

        if next_text_pos == -1 and next_png_pos == -1:
            break

        if next_text_pos != -1 and (next_text_pos < next_png_pos or next_png_pos == -1):
            length_bytes, text_bytes = text_match.groups()
            try:
                declared_len = struct.unpack('<I', length_bytes)[0]
                if len(text_bytes) > declared_len:
                    text_bytes = text_bytes[:declared_len]
                value = text_bytes.decode(errors='replace').strip()
                if value:
                    objects.append({"type": "Text", "value": value})
            except (struct.error, UnicodeDecodeError) as e:
                print(
                    f"  [!] Warning: Skipping corrupted text block at page {page_num} offset {text_match.start()}: {e}")
            cursor = text_match.end()
        elif next_png_pos != -1:
            iend_pos = page_data.find(b'IEND', next_png_pos)
            if iend_pos == -1:
                print(
                    f"  [!] Warning: Found PNG signature at page {page_num} offset {next_png_pos} but no IEND marker. Skipping.")
                cursor = next_png_pos + len(PNG_SIGNATURE)
                continue

            png_end = iend_pos + 8
            png_data = page_data[next_png_pos:png_end]

            img_index += 1
            filename = f"page{page_num}_img{img_index}.png"
            filepath = assets_dir / filename
            filepath.write_bytes(png_data)

            objects.append({"type": "Image", "file": str(filepath)})
            cursor = png_end
        else:
            break
    return objects


def parse_document(data: bytes, assets_dir: Path) -> dict[str, Any]:
    doc_structure = {
        "pages": []
    }

    page_starts = sorted(list(set([0] + [m.end() for m in PAGE_BREAK_REGEX.finditer(data)])))
    page_boundaries = page_starts + [len(data)]
    page_num = 1

    for i in range(len(page_boundaries) - 1):
        page_start, page_end = page_boundaries[i], page_boundaries[i + 1]
        if page_end - page_start < 10:
            continue
        page_data = data[page_start:page_end]
        page_objects = parse_page_simple(page_data, page_num, assets_dir)
        if page_objects:
            doc_structure["pages"].append({"page_number": page_num, "objects": page_objects})
            page_num += 1

    return doc_structure


def process_nat_file(input_file: Path, assets_dir: Path = None) -> tuple[dict[str, Any], Path]:
    base_name = input_file.with_suffix('')
    if not assets_dir:
        assets_dir = base_name.with_suffix('')

    file_data = input_file.read_bytes()

    if not assets_dir.exists():
        assets_dir.mkdir(parents=True)

    compressed_body = file_data[HEADER_LENGTH:]
    decompressed_data = None
    if not compressed_body.startswith(ZLIB_HEADER):
        header_start = file_data.find(ZLIB_HEADER)
        if header_start == -1:
            decompressed_data = file_data
        else:
            compressed_body = file_data[header_start:]

    if not decompressed_data:
        try:
            decompressed_data = zlib.decompress(compressed_body)
        except zlib.error:
            try:
                decompressed_data = zlib.decompress(compressed_body, -15)
            except zlib.error as e:
                raise RuntimeError(f"Decompression failed: {e}")

    document_structure = parse_document(decompressed_data, assets_dir)
    return document_structure, assets_dir
