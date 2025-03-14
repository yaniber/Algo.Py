<!-- File: installation.md -->
# Installation

Follow these steps to set up **Algo.Py**:

**Clone the Repository:**

   ```
   git clone https://github.com/himanshu2406/Algo.Py.git
   cd Algo.Py
   ```

**Start the Docker Container:**

   ```
   docker compose up -d
   ```

**Install Your Preferred Backtesting Engine**

   You have the following options for backtesting:
   - **vectorbt**
   - **vectorbtpro**
   - **nautilus trader** *(WIP)*

   To enable backtesting, you must install one of these libraries first.

   **Steps to Install:**

   1. **Enter the Docker Container:**

      ```
      docker exec -it algopy_app bash
      ```

   2. **Install `vectorbt` (Free Version):**
      - **Switch to the `freebt_migration` branch:**
        ```
        git checkout freebt_migration
        ```
      - **Install `vectorbt`:**
        ```
        cd vectorbt
        pip install -e .
        ```

   3. **Install `vectorbtpro`:**
      - **Clone your copy of `vectorbtpro` and install it similarly:**
        ```
        cd vectorbt.pro-main
        pip install -e .
        ```

   4. **Nautilus Trader (WIP):**
      Nautilus Trader integration is currently a work in progress and has not yet been integrated with **Algo.Py**. Stay tuned for future updates!
