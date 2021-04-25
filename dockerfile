FROM python:3
ADD launcher.py /
RUN pip install -r requirements.txt
CMD [ "python", "./launcher.py" ]
# TODO Rework this