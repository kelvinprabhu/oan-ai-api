# Docker Setup Guide for Windows

## Step 1: Install Docker Desktop for Windows

### Download and Install
1. Go to [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Download Docker Desktop for Windows
3. Run the installer (Docker Desktop Installer.exe)
4. Follow the installation wizard:
   - Enable WSL 2 feature (recommended)
   - Accept the license agreement
   - Click "Install"

### System Requirements
- Windows 10 64-bit: Pro, Enterprise, or Education (Build 19041 or higher)
- OR Windows 11 64-bit
- WSL 2 feature enabled
- Virtualization enabled in BIOS

### Post-Installation
1. Restart your computer after installation
2. Launch Docker Desktop from the Start menu
3. Wait for Docker to start (you'll see the Docker icon in the system tray)
4. Open PowerShell and verify installation:
   ```powershell
   docker --version
   docker compose version
   ```

## Step 2: Configure Docker Desktop

1. Open Docker Desktop
2. Go to Settings (gear icon)
3. **Resources** > **Advanced**:
   - Memory: Allocate at least 8GB (for Nominatim)
   - CPUs: Allocate at least 4 cores
   - Disk: Ensure at least 50GB available

## Step 3: Run Your Application

Once Docker is installed and running:

```powershell
# Navigate to your project directory
cd c:\Users\smaiv\Desktop\COSS\OAN\AI\oan-ai-api

# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Check running containers
docker ps
```

## Step 4: Verify Services

After starting, your services will be available at:
- **FastAPI App**: http://localhost:8000
- **Redis**: http://localhost:6379
- **Redis Insight**: http://localhost:8001
- **Nominatim**: http://localhost:8080
- **Marqo**: http://localhost:8882

## Troubleshooting

### Docker command not found after installation
1. Restart PowerShell/Terminal
2. Restart your computer
3. Verify Docker Desktop is running (check system tray)

### WSL 2 Installation Issues
If you need to install WSL 2 manually:
```powershell
# Run as Administrator
wsl --install
wsl --set-default-version 2
```

### Virtualization Not Enabled
1. Restart computer and enter BIOS (usually F2, F10, or Del key)
2. Find "Virtualization Technology" or "Intel VT-x" or "AMD-V"
3. Enable it
4. Save and exit BIOS

### Services Not Starting
```powershell
# Stop all containers
docker compose down

# Remove volumes (WARNING: This deletes data)
docker compose down -v

# Rebuild and start
docker compose up --build -d
```

## Alternative: Run Without Docker (Local Development)

If you prefer to run without Docker:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Note**: Running without Docker means you'll need to manually install and configure Redis, Nominatim, and Marqo.
