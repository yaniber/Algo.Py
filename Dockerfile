FROM python:3.11

WORKDIR /app

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

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --quiet --no-cache-dir 'pybind11' \
    && pip install --quiet --no-cache-dir --ignore-installed 'llvmlite' \
    && pip install --quiet --no-cache-dir --no-deps 'universal-portfolios' \
    && pip install --quiet --no-cache-dir 'pandas_datareader' \
    && pip install --quiet --no-cache-dir jupyter ipykernel supervisor

# MetaTrader5 Python package is installed separately when available (Windows only)
# No need to download MetaTrader5 terminal for Docker deployment

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