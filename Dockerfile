FROM python:3.11
RUN mkdir /bot
COPY . /bot
WORKDIR /bot
RUN pip3 install -r requirments.txt --no-cache-dir
CMD ["python", "app.py"]