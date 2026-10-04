from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / 'demo_files'
OUT_DIR.mkdir(exist_ok=True)

font = ImageFont.load_default()


def make_document(path: Path, label: str, lines: list[str]):
    img = Image.new('RGB', (1200, 900), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle((40, 40, 1160, 860), outline='#d1d5db', width=4)
    draw.text((80, 80), label, fill='#111827', font=font)
    y = 150
    for line in lines:
        draw.text((80, y), line, fill='#374151', font=font)
        y += 60
    img.save(path)

make_document(
    OUT_DIR / 'complete_id_proof.png',
    'ID Proof',
    [
        'Name: Aisha Sharma',
        'DOB: 05/11/2001',
        'Address: 25 Lake View, Bengaluru',
        'Phone: 9876543210',
    ],
)

make_document(
    OUT_DIR / 'complete_address_proof.png',
    'Address Proof',
    [
        'Address: 25 Lake View, Bengaluru',
        'Resident: Aisha Sharma',
        'Document Type: Utility Bill',
    ],
)

make_document(
    OUT_DIR / 'complete_photo.png',
    'Photograph',
    [
        'Applicant: Aisha Sharma',
        'Photo ID: 7742',
        'Verified 2026',
    ],
)

make_document(
    OUT_DIR / 'mismatch_id_proof.png',
    'ID Proof',
    [
        'Name: Aisha K. Sharma',
        'DOB: 05/11/2001',
        'Address: 25 Lake View, Bengaluru',
    ],
)

make_document(
    OUT_DIR / 'missing_document_placeholder.png',
    'Missing Document Demo',
    [
        'This is a placeholder to simulate missing files.',
        'Upload a valid ID or address proof from the app.',
    ],
)

print(f'Demo files created in {OUT_DIR}')
