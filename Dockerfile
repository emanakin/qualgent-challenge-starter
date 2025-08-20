# Updated Dockerfile (Step 3)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl unzip git python3 python3-pip openjdk-17-jre adb \
 && rm -rf /var/lib/apt/lists/*

# AndroidWorld integration (Step 3)
# RUN pip3 install --no-cache-dir \
#     numpy pandas tqdm requests \
#     android-world

# OR if installing from source:
RUN git clone https://github.com/google-research/android_world.git /workspace/android_world \
 && pip3 install -e /workspace/android_world

WORKDIR /workspace
COPY . /workspace

# Ensure results directory exists
RUN mkdir -p /workspace/results

# Default command runs the helper
CMD ["bash", "run.sh"]