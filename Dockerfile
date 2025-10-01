FROM python:3.11-slim

RUN pip install --no-cache-dir numpy matplotlib jupyter scipy plotly

# pickle and json are included in Python standard library

# Optional: set working directory
WORKDIR /app

# Optional: copy your project files
# COPY . /app

# Optional: default command
# CMD ["python", "your_script.py"]