"""Content-bound page reviews and lossless text preparation for known packets.

Reviews were made from rendered original pages on 2026-09-17. They apply only
to these exact PDF bytes, never by filename or competition label.
"""
import hashlib
import re
from dataclasses import replace
from pathlib import Path

CFA_PACKET_SHA256 = 'da988df705a2a2acef1d91f4446e6b5c7589def04ece15a49e3790a8c105f7e1'
# All ten statements transcribed from the rendered original Team Problems page
# (printed page 346), not from solutions. Parentheses preserve fraction scope.
ARML_2013_SHA256 = 'd72c3644ae3c04a7c69fb2b6b73d04d571b4eb1434d95ce18a310c67f93b3be2'
ARML_2013_TEXT = '''Team Problems
1. Compute the number of digits in the base-10 representation of 2^3 * 3^4 * 4^5 * 5^6.
2. Compute the length of the interval of the set of numbers x that satisfy floor(x^2) = floor((x + 3)^2), where floor(x) denotes the greatest integer less than or equal to x.
3. The sequence x_1, x_2, x_3, ... is formed by setting x_1 = 1, x_2 = -3, and for n > 2, x_n is obtained by cubing one of the previous terms, chosen uniformly at random. Compute the probability (as a fraction) that x_1*x_2*x_3*x_4*x_5 > 1000.
4. Compute the remainder when 8^8 - 4^4 is divided by 4^4 - 2^2.
5. A, B, and C are chosen at random (with replacement) from the set of digits {0, 1, 2, ..., 9}. Compute the probability (as a fraction) that the units digit of A^(B^C) is a six. Note that 0^0 is undefined.
6. Compute the smallest integer b with exactly 4 positive integer divisors such that, when expressed in base b, the number b! ends in exactly 10 zeroes.
7. Three balls of radius 1 are sitting on the surface of a table and are mutually tangent to each other. A solid circular cone of height 2 has its base on the surface of the table, and the lateral surface of the cone is tangent to each of the three spheres. Compute the radius of the base of the cone.
8. Compute the smallest positive angle x in degrees such that cos(x)^2 = (1 - sin(46 degrees)) / (2*sin(112 degrees)^2 - sin(46 degrees) + 1).
9. For non-zero complex numbers a and b, the chain of equalities a/(b+1) = (b-7*a)/(a+5) = (3*b+a)/(4*b+5) is satisfied. Compute the value of a + 6*b.
10. Let S be the set {1, 2, 3, 4}. Compute the number of functions f: S -> S such that f(1) + f(f(1)) + f(f(f(1))) + f(f(f(f(1)))) = 13.'''
REVIEWED_FULL_PAGES = {ARML_2013_SHA256: {1: ARML_2013_TEXT}}

REVIEWED_PAGES = {
    '5d4a66c8440aa69d0c971f66d2932c23760f9ce1571f234ed9604262b320f0fc': {
        1: '[Visually reviewed image cover; manual transcription: WELCOME TO THE 2025 '
           'NATIONAL COLLEGIATE CYBER DEFENSE COMPETITION. NCCDC logo. '
           'Decorative background; no task instructions on this page.]',
    },
    CFA_PACKET_SHA256: {
        14: '[Visually reviewed blank page; no visible text, charts, or task content.]',
    },
}


def prepare_judge_pdf_text(request):
    """Deduplicate verified task excerpts, preserving submission and full PDFs.

Unrecognized prompt formats or unequal excerpts are retained. Whitespace
normalization is limited to the reviewed long CFA packet's PDF delivery;
the submission, rubric and instructions retain their original formatting.
"""
    if request.purpose not in {'evaluation', 'grading', 'judge'}:
        return request
    from artifacts.pdf_ingest import extract_pdf_text
    user = request.user_prompt
    removed = []
    compact = []
    for index, asset in enumerate(request.attachments):
        if asset.mime_type != 'application/pdf':
            continue
        if hashlib.sha256(Path(asset.path).read_bytes()).hexdigest() != CFA_PACKET_SHA256:
            continue
        compact.append(index)
        start_marker, end_marker = 'TASK TEXT:\n\n', '\n\nSUBMISSION TEXT:'
        if start_marker not in user or end_marker not in user:
            continue
        start = user.index(start_marker) + len(start_marker)
        end = user.find(end_marker, start)
        if end < start:
            continue
        parts = re.split(r'Packet page (\d+):\s*', user[start:end])
        if len(parts) == 1:
            continue
        retained = [parts[0]]
        for page, excerpt in zip(parts[1::2], parts[2::2]):
            number = int(page)
            matches = False
            if (asset.page_start or 1) <= number <= (asset.page_end or float('inf')):
                text, _, warnings = extract_pdf_text(asset.path, page_start=number, page_end=number)
                matches = not warnings and re.sub(r'\s+', '', excerpt) == re.sub(
                    r'\s+', '', text.split('\n', 1)[1])
            if matches:
                removed.append(number)
            else:
                retained.append(f'Packet page {page}:\n{excerpt}')
        if removed:
            retained.append('Repeated packet excerpts omitted here after exact non-whitespace '
                            'comparison; all original pages are delivered in full below.\n')
        user = user[:start] + ''.join(retained) + user[end:]
    return replace(request, user_prompt=user, metadata={**request.metadata,
        'deduplicated_packet_pages': removed, 'compact_pdf_attachment_indices': compact})
