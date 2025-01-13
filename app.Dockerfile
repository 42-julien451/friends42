FROM python:3

WORKDIR /app

EXPOSE 8080

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "20", "-b", "0.0.0.0:8080", "--timeout", "600", "app:app"]
