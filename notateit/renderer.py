__author__ = 'Nikita Denissov'

import math
from pathlib import Path
from typing import List, Dict, Any

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import QRect

PADDING = 50
HEADER_FOOTER_EXTRA_PADDING = 25
MAX_WIDTH_PER_OBJECT = 800

try:
    FONT_PATH = Path("arial.ttf")
    FONT_SIZE = 48
    FONT_TITLE_SIZE = 64
    FONT = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    FONT_TITLE = ImageFont.truetype(str(FONT_PATH), FONT_TITLE_SIZE)
except IOError:
    print("Arial font not found, default font used.")
    FONT = ImageFont.load_default(size=48)
    FONT_TITLE = ImageFont.load_default(size=64)

BACKGROUND_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int):
    lines = []
    paragraphs = text.splitlines()
    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append('')
            continue
        words = paragraph.split()
        if not words:
            continue
        current_line = words[0]
        for word in words[1:]:
            if font.getbbox(current_line + " " + word)[2] <= max_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
    return "\n".join(lines)


def get_prepared_objects(page_objects: List[Dict[str, Any]], page_num: int):
    prepared_objects = []
    temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    image_counter_on_page = 0
    for i, obj in enumerate(page_objects):
        if obj['type'] == 'Image':
            image_counter_on_page += 1
            obj['value'] = f"Image {image_counter_on_page} page {page_num}"
            img_path = Path(obj['file'])
            try:
                img = Image.open(img_path)
                if img.width > MAX_WIDTH_PER_OBJECT:
                    ratio = MAX_WIDTH_PER_OBJECT / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((MAX_WIDTH_PER_OBJECT, new_height), Image.Resampling.LANCZOS)
                prepared_objects.append(
                    {'type': 'image', 'content': img, 'width': img.width, 'height': img.height, 'original_data': obj}
                )
            except FileNotFoundError:
                print(f'WARNING: Image file not found: {img_path}')
        elif obj['type'] == 'Text':
            font_to_use = FONT_TITLE if i < 2 < len(page_objects) else FONT
            wrapped_text = wrap_text(obj['value'], font_to_use, MAX_WIDTH_PER_OBJECT)
            bbox = temp_draw.multiline_textbbox((0, 0), wrapped_text, font=font_to_use)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            prepared_objects.append(
                {'type': 'text', 'content': wrapped_text, 'font': font_to_use, 'width': text_width,
                 'height': text_height, 'original_data': obj}
            )
    return prepared_objects


def render_slides(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rendered_slides = []
    for page_index, page in enumerate(data['pages']):
        page_num = page_index + 1
        interactive_objects = []

        if len(page.get('objects', [])) == 1 and page['objects'][0]['type'] == 'Image':
            img_obj = page['objects'][0]
            img_obj['value'] = f"Image 1 of {page_num}"
            img_path = Path(img_obj['file'])
            if img_path.exists():
                img = Image.open(img_path)
                interactive_objects.append({
                    'type': 'image',
                    'rect': QRect(0, 0, img.width, img.height),
                    'data': img_obj
                })
                rendered_slides.append({'image': img, 'interactive_objects': interactive_objects})
                continue

        prepared_objects = get_prepared_objects(page.get('objects', []), page_num)
        if not prepared_objects:
            slide = Image.new('RGB', (800, 600), BACKGROUND_COLOR)
            rendered_slides.append({'image': slide, 'interactive_objects': []})
            continue

        header, footer = None, None
        main_objects = list(prepared_objects)

        if main_objects and main_objects[0]['type'] == 'text':
            header = main_objects.pop(0)
            if header['font'] != FONT_TITLE:
                header['font'] = FONT_TITLE
                temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
                bbox = temp_draw.multiline_textbbox((0, 0), header['content'], font=header['font'])
                header['width'], header['height'] = bbox[2] - bbox[0], bbox[3] - bbox[1]

        if len(main_objects) > 1 and main_objects[-1]['type'] == 'text':
            footer = main_objects.pop(-1)

        grid_width, grid_height = 0, 0
        if main_objects:
            num_objects = len(main_objects)
            cols = int(math.ceil(math.sqrt(num_objects)))
            rows = int(math.ceil(num_objects / cols))
            col_widths = [0] * cols
            row_heights = [0] * rows
            for i, obj in enumerate(main_objects):
                c, r = i % cols, i // cols
                col_widths[c] = max(col_widths[c], obj['width'])
                row_heights[r] = max(row_heights[r], obj['height'])
            grid_width = sum(col_widths) + PADDING * (cols - 1)
            grid_height = sum(row_heights) + PADDING * (rows - 1)

        total_width = max(grid_width, header['width'] if header else 0, footer['width'] if footer else 0) + PADDING * 2
        total_height = PADDING
        if header:
            total_height += header['height'] + HEADER_FOOTER_EXTRA_PADDING
        if main_objects:
            total_height += grid_height + HEADER_FOOTER_EXTRA_PADDING
        if footer:
            total_height += footer['height']
        total_height += PADDING

        slide = Image.new('RGB', (int(total_width), int(total_height)), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(slide)
        current_y = PADDING

        if header:
            x_pos = (total_width - header['width']) / 2
            draw.multiline_text((x_pos, current_y), header['content'], fill=TEXT_COLOR, font=header['font'],
                                align='center')
            interactive_objects.append({
                'type': 'text',
                'rect': QRect(int(x_pos), int(current_y), int(header['width']), int(header['height'])),
                'data': header['original_data']
            })
            current_y += header['height'] + HEADER_FOOTER_EXTRA_PADDING

        if main_objects:
            grid_start_y = current_y
            num_objects = len(main_objects)
            cols = int(math.ceil(math.sqrt(num_objects)))
            rows = int(math.ceil(num_objects / cols))
            col_widths = [0] * cols
            row_heights = [0] * rows
            for i, obj in enumerate(main_objects):
                c, r = i % cols, i // cols
                col_widths[c] = max(col_widths[c], obj['width'])
                row_heights[r] = max(row_heights[r], obj['height'])
            for r in range(rows):
                grid_x_offset = (total_width - (sum(col_widths) + PADDING * (cols - 1))) / 2
                current_x = PADDING + grid_x_offset
                for c in range(cols):
                    i = r * cols + c
                    if i < num_objects:
                        obj = main_objects[i]
                        cell_width, cell_height = col_widths[c], row_heights[r]
                        x_pos = current_x + (cell_width - obj['width']) / 2
                        y_pos = grid_start_y + (cell_height - obj['height']) / 2
                        if obj['type'] == 'image':
                            slide.paste(obj['content'], (int(x_pos), int(y_pos)))
                        elif obj['type'] == 'text':
                            draw.multiline_text((x_pos, y_pos), obj['content'], fill=TEXT_COLOR, font=obj['font'],
                                                align='center')
                        interactive_objects.append({
                            'type': obj['type'],
                            'rect': QRect(int(x_pos), int(y_pos), int(obj['width']), int(obj['height'])),
                            'data': obj['original_data']
                        })
                    current_x += col_widths[c] + PADDING
                grid_start_y += row_heights[r] + PADDING
            current_y += grid_height + HEADER_FOOTER_EXTRA_PADDING

        if footer:
            x_pos = (total_width - footer['width']) / 2
            draw.multiline_text((x_pos, current_y), footer['content'], fill=TEXT_COLOR, font=footer['font'],
                                align='center')
            interactive_objects.append({
                'type': 'text',
                'rect': QRect(int(x_pos), int(current_y), int(footer['width']), int(footer['height'])),
                'data': footer['original_data']
            })

        rendered_slides.append({'image': slide, 'interactive_objects': interactive_objects})
    return rendered_slides
