FROM python:3.11-slim AS build

USER root

WORKDIR /app/

RUN apt-get update && apt-get install -y sudo

# Copiar todo o que esta dentro da pasta
COPY . .
RUN pip install --user --no-cache-dir --no-warn-script-location -r requirements.txt
#RUN pip install -r requirements.txt

# Exponer el puerto
EXPOSE 8080

# Comando para ejecutar el servidor
CMD ["python", "main.py"]
