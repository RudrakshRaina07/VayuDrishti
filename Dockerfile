FROM pathwaycom/pathway:latest

WORKDIR /app

COPY pathway_stream.py .

CMD ["python", "pathway_stream.py"]
