from io import BytesIO
from reportlab.pdfgen import canvas
from docx import Document
from app import create_app, db
from app.models import Resume, User
from werkzeug.security import generate_password_hash

app = create_app('testing')
with app.app_context():
    db.create_all()
    email = 'bugfix_test@example.com'
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            full_name='Bug Fix Test',
            username='bugfixtest',
            email=email,
            phone='1234567890',
            password_hash=generate_password_hash('Password123!'),
        )
        db.session.add(user)
        db.session.commit()

    client = app.test_client()
    client.post(
        '/auth/login',
        data={'email': email, 'password': 'Password123!', 'remember_me': 'y', 'submit': 'Login'},
        follow_redirects=True,
    )

    def upload_file(filename, content, content_type='application/octet-stream'):
        return client.post(
            '/resume/',
            data={'resume_file': (BytesIO(content), filename), 'submit': 'Upload Resume'},
            content_type='multipart/form-data',
            follow_redirects=True,
        )

    # PDF upload
    pdf_buf = BytesIO()
    c = canvas.Canvas(pdf_buf)
    c.drawString(100, 750, 'PDF Test')
    c.save()
    pdf_buf.seek(0)
    pdf_resp = upload_file('test.pdf', pdf_buf.read(), 'application/pdf')
    print('pdf upload', pdf_resp.status_code, b'Resume uploaded and text extracted successfully.' in pdf_resp.data)

    # DOCX upload
    docx_buf = BytesIO()
    document = Document()
    document.add_paragraph('DOCX test content')
    document.save(docx_buf)
    docx_buf.seek(0)
    docx_resp = upload_file(
        'test.docx',
        docx_buf.read(),
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    print('docx upload', docx_resp.status_code, b'Resume uploaded and text extracted successfully.' in docx_resp.data)

    # TXT upload
    txt_resp = upload_file('test.txt', b'Plain text content', 'text/plain')
    print('txt rejected', txt_resp.status_code, b'Only PDF and DOCX files are supported.' in txt_resp.data)

    # PY upload
    py_resp = upload_file('test.py', b"print('hello')", 'text/x-python')
    print('py rejected', py_resp.status_code, b'Only PDF and DOCX files are supported.' in py_resp.data)

    # ZIP upload
    zip_resp = upload_file('test.zip', b'PK\x03\x04\x14\x00', 'application/zip')
    print('zip rejected', zip_resp.status_code, b'Only PDF and DOCX files are supported.' in zip_resp.data)

    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.upload_time.desc()).first()
    if resume:
        response1 = client.post(f'/resume/interview-questions/{resume.id}', data={'submit': 'Regenerate'}, follow_redirects=True)
        response2 = client.post(f'/resume/interview-questions/{resume.id}', data={'submit': 'Regenerate'}, follow_redirects=True)
        q1 = [line.strip() for line in response1.data.split(b'<li>') if b'</li>' in line]
        q2 = [line.strip() for line in response2.data.split(b'<li>') if b'</li>' in line]
        print('regenerate different', q1 != q2)
    else:
        print('no resume available for regeneration test')
