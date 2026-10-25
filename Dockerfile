
FROM python:3.11-slim

WORKDIR /home/myapp

COPY app.py /home/myapp/
COPY templates/ /home/myapp/templates/

RUN pip install --no-cache-dir flask

EXPOSE 8080

CMD ["python", "/home/myapp/app.py"]
