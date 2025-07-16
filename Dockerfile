FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

# Install OCR and system libraries if needed (keep tesseract lines if you use OCR; can remove if not)
RUN apt-get update && \
    apt-get install -y tesseract-ocr libtesseract-dev libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libx11-xcb1 xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install all Playwright browsers and dependencies
RUN playwright install
RUN playwright install-deps
RUN playwright install firefox

# Clean up any lingering profiles (optional)
RUN rm -rf /app/profile

# Copy all code last (so Docker cache works)
COPY . .

ENV PYTHONUNBUFFERED=1

# By default, run your example script under xvfb (for headful Playwright)
# CMD ["sh", "-c", "xvfb-run -a python ./example_usage.py"]
CMD ["sh", "-c", "xvfb-run -a python ./example_usage_text_input.py"]

