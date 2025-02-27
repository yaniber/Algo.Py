# Use Python 3.10 (pre-built wheels for statsmodels 0.13.2 work out of the box)
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install system dependencies and tools (including wget for ta-lib download)
RUN apt-get update && \
    apt-get install -yq --no-install-recommends cmake wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Build and install ta-lib
RUN wget https://netcologne.dl.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr --build=unknown-unknown-linux && \
  make && \
  make install

RUN rm -R ta-lib ta-lib-0.4.0-src.tar.gz

RUN pip install --no-cache-dir TA-Lib==0.4.32

# Install uv (the pip alternative with enhanced dependency resolution)
RUN pip install --no-cache-dir uv

# Copy your requirements file (or better, a uv lockfile if you generate one)
COPY requirements.txt .

RUN uv pip install --system -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# (Optional) Install additional packages if needed—for example, kaleido for plotly export
RUN pip install --no-cache-dir kaleido

# (Optional) Setup Jupyter kernel if you need interactive development
RUN pip install --no-cache-dir jupyter ipykernel && \
    python -m ipykernel install --user --name=python3 --display-name "Python 3"

# Ensure your application code is on PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Keep the container running
CMD ["tail", "-f", "/dev/null"]