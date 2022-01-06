FROM nginx/unit:1.26.1-python3.9
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY nginxunit.config.json /docker-entrypoint.d/config.json
COPY app .