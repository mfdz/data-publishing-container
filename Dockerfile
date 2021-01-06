FROM python:3.9

WORKDIR /usr/src/app

ENV DPC_MDM_CERT="PATH_TO_CERT:PASSWORD"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "python" ]
CMD [ "/usr/local/bin/doit" ]
