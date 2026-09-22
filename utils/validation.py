"""Validation utilities."""
def validate_pdf(file_bytes, filename):
    if not filename.lower().endswith('.pdf'):
        return False, 'Only PDF files are allowed.'
    if not file_bytes:
        return False, 'The uploaded file is empty.'
    return True, 'PDF passed basic validation.'
