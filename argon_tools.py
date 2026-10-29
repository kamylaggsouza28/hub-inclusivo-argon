"""Validation, visual maps and portable exports, without external executables."""
import html
import json
import textwrap
from io import BytesIO
from pathlib import Path

import reportlab
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

FONT_PATH = Path(reportlab.__file__).parent / 'fonts' / 'Vera.ttf'
pdfmetrics.registerFont(TTFont('ArgonVera', str(FONT_PATH)))


def validate(data, kind):
    fields = {'mapa': ('ramos', ('titulo', 'detalhes')), 'infografico': ('cartoes', ('titulo', 'texto', 'exemplo')), 'video': ('cenas', ('tempo', 'visual', 'audio'))}
    key, required = fields[kind]
    if not isinstance(data, dict) or not isinstance(data.get('titulo'), str):
        raise ValueError('Informe um título em texto.')
    items = data.get(key)
    if not isinstance(items, list) or not 1 <= len(items) <= 30:
        raise ValueError('Use entre 1 e 30 blocos.')
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Cada bloco deve ser um objeto.')
        for field in required:
            value = item.get(field)
            if field == 'detalhes':
                if not isinstance(value, list) or len(value) > 30 or any(not isinstance(v, str) or len(v) > 4000 for v in value):
                    raise ValueError('Detalhes devem ser uma lista de até 30 textos curtos.')
            elif not isinstance(value, str) or len(value) > 4000:
                raise ValueError(f'O campo {field} deve ser texto de até 4000 caracteres.')
    return data


def lines(data):
    result = [str(data.get('titulo', 'Material Argon'))]
    for key, value in data.items():
        if key == 'titulo':
            continue
        if isinstance(value, list):
            for index, item in enumerate(value, 1):
                result.append(f'{index}.')
                if isinstance(item, dict):
                    for label, content in item.items():
                        result.append(f'{label}: ' + ('; '.join(content) if isinstance(content, list) else str(content)))
                else:
                    result.append(str(item))
        else:
            result.append(f'{key}: {value}')
    return result


def pdf_bytes(data):
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles['Title'].fontName = 'ArgonVera'
    styles['BodyText'].fontName = 'ArgonVera'
    story = []
    for i, line in enumerate(lines(data)):
        story.extend([Paragraph(html.escape(line), styles['Title' if i == 0 else 'BodyText']), Spacer(1, 10)])
    SimpleDocTemplate(output).build(story)
    return output.getvalue()


def png_bytes(data):
    font = ImageFont.truetype(str(FONT_PATH), size=22)
    if 'ramos' in data:
        blocks = []
        for branch in data['ramos']:
            content = [branch['titulo']] + ['• ' + detail for detail in branch['detalhes']]
            blocks.append([line for text in content for line in (textwrap.wrap(text, 52) or [''])])
        height = 80 + sum(max(100, len(block) * 32 + 28) + 24 for block in blocks)
        if height > 30000:
            raise ValueError('Mapa muito extenso para PNG; utilize PDF ou JSON.')
        canvas = Image.new('RGB', (1300, height), 'white')
        draw = ImageDraw.Draw(canvas)
        center = height // 2
        draw.rounded_rectangle((20, center - 100, 380, center + 100), radius=15, outline='#183044', width=3)
        title = textwrap.wrap(data['titulo'], 23)
        if len(title) > 5:
            raise ValueError('Encurte o título do mapa para exportar PNG.')
        for i, line in enumerate(title):
            draw.text((38, center - 75 + i * 30), line, font=font, fill='#183044')
        y = 40
        for block in blocks:
            box_height = max(100, len(block) * 32 + 28)
            draw.line((380, center, 460, y + box_height // 2), fill='#183044', width=3)
            draw.rounded_rectangle((460, y, 1280, y + box_height), radius=15, outline='#183044', width=3)
            for i, line in enumerate(block):
                draw.text((480, y + 14 + i * 32), line, font=font, fill='#183044')
            y += box_height + 24
        output = BytesIO()
        canvas.save(output, format='PNG')
        return output.getvalue()
    wrapped = [part for line in lines(data) for part in (textwrap.wrap(line, 76) or [''])]
    height = 60 + 34 * len(wrapped)
    if height > 30000:
        raise ValueError('Material muito extenso para PNG; utilize PDF ou JSON.')
    canvas = Image.new('RGB', (1100, height), '#ffffff')
    draw = ImageDraw.Draw(canvas)
    for i, line in enumerate(wrapped):
        draw.text((28, 25 + i * 34), line, font=font, fill='#183044')
    output = BytesIO()
    canvas.save(output, format='PNG')
    return output.getvalue()


def map_dot(data):
    quote = lambda value: json.dumps(str(value), ensure_ascii=False)
    rows = ['digraph Argon {', 'graph [rankdir=LR];', 'node [shape=box, style=rounded];', f'root [label={quote(data["titulo"])}];']
    for i, branch in enumerate(data['ramos']):
        rows.extend([f'b{i} [label={quote(branch["titulo"])}];', f'root -> b{i};'])
        for j, detail in enumerate(branch['detalhes']):
            rows.extend([f'd{i}_{j} [label={quote(detail)}];', f'b{i} -> d{i}_{j};'])
    return '\n'.join(rows + ['}'])
