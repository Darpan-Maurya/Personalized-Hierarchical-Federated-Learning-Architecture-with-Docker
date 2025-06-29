FROM python:3.10-slim

WORKDIR /app

COPY cloud.py .
COPY static /app/static


RUN pip install flask requests

EXPOSE 5013

CMD ["python", "cloud.py"]
