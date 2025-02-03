FROM python:3.9-slim
WORKDIR /app
# Upgrade pip to the latest version
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]