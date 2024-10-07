# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Install system dependencies required by Playwright and Chromium
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libxshmfence1 \
    fonts-liberation \
    libwoff1 \
    libjpeg62-turbo \
    libcairo2 \
    libdatrie1 \
    libgraphite2-3 \
    libharfbuzz0b \
    libpango-1.0-0 \
    libthai0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxcursor1 \
    libxi6 \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Set environment variable to ensure browsers are installed in the project directory
ENV PLAYWRIGHT_BROWSERS_PATH=0

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN pip install --no-cache-dir playwright && \
    playwright install chromium

# Copy the rest of the application code
COPY . .

# Expose the port the app will run on
EXPOSE 8080

# Command to start the app using Flask on port 8080
CMD ["python", "main.py"]
