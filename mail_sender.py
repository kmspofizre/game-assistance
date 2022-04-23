import smtplib
import mimetypes
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(email, subjects, text, attachments):
    addr_from = os.getenv("FROM")
    password = os.getenv("PASSWORD")

    msg = MIMEMultipart()
    msg['From'] = addr_from
    msg['To'] = email
    msg['Subject'] = subjects
    msg_text = f"Hello!\nYou need to verify your mail\nHere is the link:\n{text}"
    msg_html = f"""\
    <html>
      <head></head>
      <body>
        <div style="text-align:center; font-family: sans-serif;">
            <span style="font-size: 25px;">Hello!</span><br>
            <span style="font-size: 18px">You need to verify your account - <a href="{text}">link</a></span>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(msg_html, 'html'))
    process_attachments(msg, attachments)
    server = smtplib.SMTP_SSL(os.getenv('HOST'), os.getenv('PORT'))
    server.login(addr_from, password)  # авторизация на сервере

    server.send_message(msg)  # отправка сообщения
    server.quit()  # выход с серва
    return True


def process_attachments(msg, attachments):
    for f in attachments:
        if os.path.isfile(f):
            attach_file(msg, f)
        elif os.path.exists(f):
            dir = os.listdir(f)
            for file in dir:
                if os.path.isfile(file):
                    attach_file(msg, f + '/' + file)


def attach_file(msg, f):
    attach_types = {
        'text': MIMEText,
        'image': MIMEImage,
    }
    filename = os.path.basename(f)
    ctype, encoding = mimetypes.guess_type(f)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    print(f, maintype, subtype, ctype)
    with open(f, mode='rb' if maintype != 'text' else 'r') as fp:
        if maintype in attach_types:
            file = attach_types[maintype](fp.read(), _subtype=subtype)
        else:
            file = MIMEBase(maintype, subtype)
            file.set_payload(fp.read())
            encoders.encode_base64(file)
    file.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(file)