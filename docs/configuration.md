<!-- File: configuration.md -->
# Basic Configuration

This section covers the basic configuration steps for **Algo.Py**.

## Environment Setup

- Ensure you have a suitable Python environment.
- Clone the repository and install all required dependencies.
- Set environment variables in the `config/.env` file. For example:

```bash
# Example configuration settings
API_KEY=your_api_key
API_SECRET=your_api_secret
OMS_TYPE=binance  # Options: telegram, zerodha, binance
```

## Dashboard and OMS Settings

- The dashboard configuration is managed in the Streamlit application (`Dashboard/main_dash.py`).
- OMS credentials and settings are provided via configuration files.
- Additional options are detailed in the Advanced Topics section.
