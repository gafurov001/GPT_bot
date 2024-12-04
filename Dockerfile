FROM python:3.11-slim


# Set the working directory
WORKDIR /app

# Copy the application code
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install -r requirements.txt

# Command to run the application
CMD ["python", "main.py"]
