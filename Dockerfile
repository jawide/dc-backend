FROM python:alpine AS environment
EXPOSE 5000

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN python init.py
ENTRYPOINT /usr/local/bin/flask run -h 0.0.0.0 -p 5000 > /app/log/flask.log