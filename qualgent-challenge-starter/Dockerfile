# Minimal container for android_world runner + ADB
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip git python3 python3-pip openjdk-17-jre adb \
 && rm -rf /var/lib/apt/lists/*

# android_world deps (placeholder - pin in your real impl)
RUN pip3 install --no-cache-dir \    numpy pandas tqdm requests

WORKDIR /workspace
COPY . /workspace

# Default command runs the helper
CMD ["bash", "run.sh"]
