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

# Install Wine for MetaTrader5 support on Linux (comprehensive setup)
RUN dpkg --add-architecture i386 && \
 apt-get update && \
 apt-get install -yq --no-install-recommends \
 wine \
 wine32 \
 wine64 \
 supervisor \
 && apt-get clean && \
 rm -rf /var/lib/apt/lists/*

# Install winetricks separately if available
RUN wget -O /usr/local/bin/winetricks https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks && \
 chmod +x /usr/local/bin/winetricks || echo "Winetricks installation skipped"

# Install TA-Lib native library for technical analysis
RUN apt-get update && \
 apt-get install -y build-essential && \
 wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
 tar -xzf ta-lib-0.4.0-src.tar.gz && \
 cd ta-lib/ && \
 ./configure --prefix=/usr && \
 make && \
 make install && \
 cd .. && rm -rf ta-lib* && \
 apt-get clean && \
 rm -rf /var/lib/apt/lists/*

# Configure Wine environment for MetaTrader5 (comprehensive setup)
ENV WINEARCH=win64
ENV WINEPREFIX=/app/.wine
ENV DISPLAY=:99
ENV WINEDLLOVERRIDES="mscoree,mshtml="

# Create directory for Wine data (initialization happens at runtime)
RUN mkdir -p /app/.wine

# Copy MT5 setup script
COPY scripts/setup_mt5_wine.sh /app/scripts/
RUN chmod +x /app/scripts/setup_mt5_wine.sh

COPY requirements.txt .

# Configure pip for better reliability in Docker builds
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_RETRIES=3
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Fix SSL certificate issues with pip in restricted environments
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY . .

# Install additional packages with better error handling and no conflicts
# Note: supervisor already installed via apt-get, so not installing via pip
RUN pip install --quiet --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org jupyter ipykernel || \
    (echo "Failed to install jupyter/ipykernel, retrying..." && \
     pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org jupyter ipykernel)

# Install scientific packages that may need special handling
RUN pip install --quiet --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org 'pybind11' || \
    (echo "pybind11 installation failed, continuing..." && exit 0)

RUN pip install --quiet --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --ignore-installed 'llvmlite' || \
    (echo "llvmlite installation failed, continuing..." && exit 0)

RUN pip install --quiet --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-deps 'universal-portfolios' || \
    (echo "universal-portfolios installation failed, continuing..." && exit 0)

RUN pip install --quiet --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org 'pandas_datareader' || \
    (echo "pandas_datareader installation failed, continuing..." && exit 0)

# MetaTrader5 can be installed via Wine for Linux compatibility
# Use /app/scripts/setup_mt5_wine.sh to complete the setup when needed
# The Python package still requires manual installation in Wine environment

COPY supervisord.conf /etc/supervisord.conf

RUN python -m ipykernel install --user --name=python3 --display-name "Python 3"

ARG BACKTEST_BACKEND
RUN if [ "$BACKTEST_BACKEND" = "vectorbt" ]; then \
    echo "Installing vectorbt..." && \
    pip install -U --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org vectorbt || \
    (echo "vectorbt installation failed, trying with more memory..." && \
     pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org vectorbt); \
    elif [ "$BACKTEST_BACKEND" = "vectorbtpro" ]; then \
    echo "Installing vectorbtpro..." && \
    pip install -U --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org "vectorbtpro[base] @ git+https://github.com/polakowo/vectorbt.pro.git" || \
    (echo "vectorbtpro installation failed, trying alternative approach..." && \
     pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org "git+https://github.com/polakowo/vectorbt.pro.git"); \
    fi

ENV PYTHONPATH="/app"

EXPOSE 8501
EXPOSE 8888
EXPOSE 1234

CMD ["supervisord", "-c", "/etc/supervisord.conf"]