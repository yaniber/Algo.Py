FROM python:3.11

WORKDIR /app

# Install system dependencies including Wine for MetaTrader5 support
RUN apt-get update && \
 apt-get install -yq --no-install-recommends \
 cmake \
 wget \
 gnupg2 \
 apt-transport-https \
 ca-certificates \
 xvfb \
 && apt-get clean && \
 rm -rf /var/lib/apt/lists/*

# Install Wine for MetaTrader5 support on Linux (minimal setup)
RUN dpkg --add-architecture i386 && \
 apt-get update && \
 apt-get install -yq --no-install-recommends \
 wine \
 && apt-get clean && \
 rm -rf /var/lib/apt/lists/*

RUN wget https://netcologne.dl.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr --build=unknown-unknown-linux && \
  make && \
  make install

RUN rm -R ta-lib ta-lib-0.4.0-src.tar.gz

RUN pip install --no-cache-dir TA-Lib==0.4.32

# Configure Wine environment for MetaTrader5 (optional)
ENV WINEARCH=win64
ENV WINEPREFIX=/app/.wine
ENV DISPLAY=:99

# Create wine user and initialize basic Wine environment
RUN useradd -m -s /bin/bash wineuser && \
 chown -R wineuser:wineuser /app

# Initialize Wine environment (basic setup only)
RUN su - wineuser -c "cd /app && \
 export WINEARCH=win64 && \
 export WINEPREFIX=/app/.wine && \
 echo 'Wine environment prepared for MT5'" || echo "Wine preparation completed"

# Change ownership back to root
RUN chown -R root:root /app

# Copy MT5 setup script
COPY scripts/setup_mt5_wine.sh /app/scripts/
RUN chmod +x /app/scripts/setup_mt5_wine.sh

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --quiet --no-cache-dir 'pybind11' \
    && pip install --quiet --no-cache-dir --ignore-installed 'llvmlite' \
    && pip install --quiet --no-cache-dir --no-deps 'universal-portfolios' \
    && pip install --quiet --no-cache-dir 'pandas_datareader' \
    && pip install --quiet --no-cache-dir jupyter ipykernel supervisor

# MetaTrader5 can be installed via Wine for Linux compatibility
# Use /app/scripts/setup_mt5_wine.sh to complete the setup when needed
# The Python package still requires manual installation in Wine environment

COPY supervisord.conf /etc/supervisord.conf

RUN python -m ipykernel install --user --name=python3 --display-name "Python 3"

ARG BACKTEST_BACKEND
RUN if [ "$BACKTEST_BACKEND" = "vectorbt" ]; then \
    pip install -U --no-cache-dir vectorbt; \
    elif [ "$BACKTEST_BACKEND" = "vectorbtpro" ]; then \
    pip install -U "vectorbtpro[base] @ git+https://github.com/polakowo/vectorbt.pro.git"; \
    fi

ENV PYTHONPATH="${PYTHONPATH}:/app"

EXPOSE 8501
EXPOSE 8888

CMD ["supervisord", "-c", "/etc/supervisord.conf"]