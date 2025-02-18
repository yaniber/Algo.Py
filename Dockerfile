# Use the official Python 3.11 image as a base
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for ta-lib
RUN apt-get update && \
 apt-get install -yq --no-install-recommends cmake && \
 apt-get clean && \
 rm -rf /var/lib/apt/lists/*

RUN wget https://netcologne.dl.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr --build=unknown-unknown-linux && \
  make && \
  make install

RUN rm -R ta-lib ta-lib-0.4.0-src.tar.gz

RUN pip install --no-cache-dir TA-Lib==0.4.32

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Install BTengine in editable mode
RUN pip install --quiet --no-cache-dir \
    'plotly>=5.0.0' \
    'kaleido'

RUN pip install --quiet --no-cache-dir 'pybind11'
RUN pip install --quiet --no-cache-dir --ignore-installed 'llvmlite'

RUN pip install --quiet --no-cache-dir \
    'numpy==1.24.2' \
    'pandas>=1.5.0' \
    'numba==0.60.0' \
    'schedule' \
    'ipywidgets>=7.0.0' \
    'python-dateutil' \
    'dateparser' \
    'imageio' \
    'mypy_extensions' \
    'humanize' \
    'attrs>=21.1.0' \
    'websocket-client' \
    'yfinance>=0.2.20' \
    'python-binance>=1.0.16' \
    'alpaca-py' \
    'ccxt>=1.89.14' \
    'tables' \
    'SQLAlchemy>=2.0.0' \
    'duckdb' \
    'duckdb-engine' \
    'pyarrow' \
    'polygon-api-client>=1.0.0' \
    'beautifulsoup4' \
    'nasdaq-data-link' \
    'alpha_vantage' \
    'databento'  \
    'technical' \
    'numexpr' \
    'hyperopt' \
    'optuna' \
    'pathos' \
    'mpire' \
    'dask' \
    'ray>=1.4.1' \
    'plotly-resampler' \
    'quantstats>=0.0.37' \
    'PyPortfolioOpt>=1.5.1' \
    'Riskfolio-Lib>=3.3.0' \
    'python-telegram-bot>=13.4' \
    'dill' \
    'lz4' \
    'blosc2' \
    'ta' \
    'pandas_ta' \
    'tabulate'

RUN pip install --quiet --no-cache-dir --no-deps 'universal-portfolios'
RUN pip install --quiet --no-cache-dir 'pandas_datareader'

# Install Jupyter and ipykernel
RUN pip install --quiet --no-cache-dir jupyter ipykernel

# Add the Python environment as a Jupyter kernel
RUN python -m ipykernel install --user --name=python3 --display-name "Python 3"

# Set the PYTHONPATH environment variable
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Command to keep the container running
CMD ["tail", "-f", "/dev/null"]

# might need to add apt update && apt install -y python3 python3-dev g++ pybind11-dev