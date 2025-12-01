# Deploying MT5 Service on Windows VPS

Follow these steps to deploy the MT5 API service on your Windows VPS.

## Prerequisites
1.  **MetaTrader 5 Terminal**: Must be installed and running on the VPS.
2.  **Python 3.10+**: Must be installed. Ensure "Add Python to PATH" is checked during installation.

## Deployment Steps

1.  **Copy Files**:
    Copy the entire `mt5_service` folder to your VPS (e.g., to `C:\Reki\mt5_service`).
    Ensure the folder contains:
    - `main.py`
    - `requirements.txt`
    - `.env.example`
    - `start_service.ps1`

2.  **Configure Environment**:
    - Rename `.env.example` to `.env`.
    - Open `.env` with Notepad.
    - Fill in your MT5 credentials (`MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`).
    - Save the file.

3.  **Run the Service**:
    - Right-click `start_service.ps1` and select "Run with PowerShell".
    - OR open PowerShell, navigate to the folder, and run:
      ```powershell
      .\start_service.ps1
      ```

4.  **Verify**:
    - The script should install dependencies and start the server.
    - You should see: `Starting FastAPI server on http://0.0.0.0:8000`.
    - Keep this window open.

## Troubleshooting
- **MT5 Connection Failed**: Ensure MT5 terminal is running and "Algo Trading" is enabled in the toolbar.
- **Dependency Errors**: Try running `pip install -r requirements.txt` manually in PowerShell.
