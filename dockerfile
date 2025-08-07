FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]



# FROM python:3.13-alpine

# # Install system dependencies
# RUN apk update && apk add --no-cache \
#     gcc \
#     musl-dev \
#     libffi-dev \
#     openssl-dev \
#     python3-dev \
#     jpeg-dev \
#     zlib-dev \
#     postgresql-dev \
#     build-base

# # Set working directory
# WORKDIR /app

# # Copy and install requirements
# COPY requirements.txt .
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt

# # Copy project files
# COPY . .

# # Expose port
# EXPOSE 8000

# # Run server
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
