FROM python:3.9
WORKDIR /bot
COPY . . 
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
CMD ["python3", "bot.py"]
