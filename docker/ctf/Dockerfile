FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ make binutils file curl netcat-openbsd openssl unzip p7zip-full gdb socat tcpdump libc6-i386 lib32stdc++6 xxd libimage-exiftool-perl php-cli && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /opt/ctf/requirements.txt
RUN pip install --no-cache-dir -r /opt/ctf/requirements.txt && pip check
ENV TERM=xterm
COPY check_dependencies.py /opt/ctf/check_dependencies.py
RUN python /opt/ctf/check_dependencies.py
WORKDIR /workspace
CMD ["sleep", "infinity"]
