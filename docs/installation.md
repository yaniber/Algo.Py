<!-- File: installation.md -->
# Installation

Follow these steps to set up **Algo.Py**:

**Clone the Repository:**

   ```
   git clone https://github.com/himanshu2406/Algo.Py.git
   cd Algo.Py
   ```

**Select your Backtesting Backend:**

   Change your backtest backend to be installed in the `docker-compose.yml` file

   The default is set to 'vectorbt' [Options : 'vectorbt' , 'vectorbtpro', 'nautilus' (coming soon)]
   ```
   args:
      - BACKTEST_BACKEND=vectorbt
   ```

   Note : In case `vectorbtpro` is chosen , change your .env appropriately : 

   ```
   BACKTEST_BACKEND=vectorbtpro
   ```

**Start the Docker Container:**

   ```
   docker compose up -d
   ```

**More information on Backtest Backends**

   You have the following options for backtesting:
   - **vectorbt**
   - **vectorbtpro**
   - **nautilus trader** *(WIP)*

   To enable backtesting, you must install one of these libraries first.
   This is done during the docker build process by selecting the appropriate option from available Backtest Backends.

   However , if you've installed `vectorbt` and want to migrate to `vectorbtpro` instead , you can do this easily - 

   **Steps to Re-Install:**

   1. **Enter the Docker Container:**

      ```
      docker exec -it algopy_app bash
      ```

   2. **Uninstall `vectorbt` (Free Version):**

        ```
        pip uninstall vectorbt
        ```

   3. **Install `vectorbtpro`:**
      - **Clone your copy of `vectorbtpro` and install it:**
        ```
        cd vectorbt.pro-main
        pip install -e .
        ```
   
   4. **Change your .env**

      ```
      BACKTEST_BACKEND=vectorbtpro
      ```

   **Nautilus Trader (WIP):**
      Nautilus Trader integration is currently a work in progress and has not yet been integrated with **Algo.Py**. Stay tuned for future updates!
