FROM python:3.10-slim

WORKDIR /app

COPY edge.py .
COPY static /app/static


RUN pip install flask requests

EXPOSE 5000

CMD ["python", "edge.py"]
