FROM python:3.8 as builder
COPY requirements.txt .


RUN pip install --user -r requirements.txt



ENV HOST=smtp.yandex.ru
ENV PORT=465
ENV FROM=CheckMailG@yandex.ru
ENV PASSWORD=awuzdpxtmtdebtmh


CMD ["python", "-u", "./main.py"]