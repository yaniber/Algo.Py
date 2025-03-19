import os
import sys
import importlib
import builtins
from dotenv import load_dotenv

load_dotenv(dotenv_path='config/.env')

backend = os.getenv("BACKTEST_BACKEND", "vectorbt").lower()

available_backends = {
    "vectorbt": "vectorbt",
    "vectorbtpro": "vectorbtpro",
    "nautilus": "nautilus",  # Not available yet.
}

if backend not in available_backends:
    backend = "vectorbt"

module_name = available_backends[backend]

try:
    mod = importlib.import_module(module_name)
except ImportError:
    raise ImportError(f"Could not import module '{module_name}'. Make sure it is installed.")

sys.modules["abstractbt"] = mod

setattr(builtins, "BACKTEST_BACKEND", backend)
