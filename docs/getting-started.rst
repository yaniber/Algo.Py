Getting Started
===============

Installation
------------
1. Clone the repository:
   .. code-block:: bash

      git clone https://github.com/himanshu2406/Algo.Py.git
      cd Algo.Py

2. Start the Docker container:
   .. code-block:: bash

      docker compose up -d

Accessing the Dashboard
-----------------------
1. Connect to the running container:
   .. code-block:: bash

      # Either attach directly
      docker exec -it algopy_app /bin/bash
      
      # Or use VS Code's "Attach to Container" feature

2. Navigate to app directory and launch dashboard:
   .. code-block:: bash

      cd /app
      streamlit run Dashboard/main_dash.py

   The dashboard will be available at ``http://localhost:8501``.

   .. image:: /assets/dashboard-screenshot.png
      :alt: Algo.Py Dashboard Preview
      :width: 800
      :align: center

.. note::
   - Default port mappings: 8501 (Streamlit)
