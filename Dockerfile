FROM python:latest

RUN apt update -y && apt upgrade -y

SHELL ["/bin/bash", "-c"]

ARG GROQ_API_KEY

COPY . .

RUN python3 -m venv venv

RUN source venv/bin/activate

RUN pip3 install -r requirements.txt

RUN export GROQ_API_KEY=${GROQ_API_KEY}

ENV PORT=8501

EXPOSE 8501

ENTRYPOINT [ "streamlit", "run", "app.py" ]
