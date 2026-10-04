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
    OUT_DIR / 'identity_proof_complete.png',
    'Identity Proof',
    [
        'Name: Aisha Sharma',
        'DOB: 05/11/2001',
        'Address: 25 Lake View, Bengaluru',
        'Aadhaar Number: 1234 5678 9012',
    ],
)

make_document(
    OUT_DIR / 'student_id_complete.png',
    'Student ID',
    [
        'Student ID: 2024-CS-077',
        'Name: Aisha Sharma',
        'College: NIT Trichy',
        'Course: Computer Science',
    ],
)

make_document(
    OUT_DIR / 'marksheet_complete.png',
    'Marksheet',
    [
        'Name: Aisha Sharma',
        'Institution: NIT Trichy',
        'Course: Computer Science',
        'Percentage: 92%',
        'Academic Year: 2026',
    ],
)

make_document(
    OUT_DIR / 'income_certificate_complete.png',
    'Income Certificate',
    [
        'Name: Aisha Sharma',
        'Annual Family Income: ₹1,20,000',
        'Issued by: District Welfare Office',
    ],
)

make_document(
    OUT_DIR / 'address_proof_complete.png',
    'Address Proof',
    [
        'Address: 25 Lake View, Bengaluru',
        'Resident: Aisha Sharma',
        'State: Karnataka',
    ],
)

make_document(
    OUT_DIR / 'bank_proof_complete.png',
    'Bank Proof',
    [
        'Name: Aisha Sharma',
        'Bank: HDFC Bank',
        'IFSC: HDFC0001234',
    ],
)

make_document(
    OUT_DIR / 'income_certificate_missing_demo.png',
    'Income Certificate',
    [
        'This sample is intentionally missing the income certificate text.',
        'Used to demo missing-document handling.',
    ],
)

make_document(
    OUT_DIR / 'mismatch_marksheet.png',
    'Marksheet',
    [
        'Name: Aisha K Sharma',
        'Institution: NIT Trichy',
        'Course: Computer Science',
        'Percentage: 92%',
    ],
)

make_document(
    OUT_DIR / 'unreadable_doc.png',
    'Unreadable Document',
    [
        '??',
        '???',
        'No readable text detected',
    ],
)

make_document(
    OUT_DIR / 'unknown_document.png',
    'Random Document',
    [
        'This is not a valid scheme document',
        'No institution or income details found',
    ],
)

print(f'Demo files created in {OUT_DIR}')
