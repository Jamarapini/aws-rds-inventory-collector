# 🚀 AWS RDS Inventory Dashboard - Windows Server 2019 EC2 Deployment Guide

Complete step-by-step guide to deploy the Streamlit dashboard on a Windows Server 2019 EC2 instance.

---

## 📋 Prerequisites

- **EC2 Instance** running Windows Server 2019
- **Admin access** to the EC2 instance
- **RDS Database** with inventory data already loaded
- **`.env` file** with database credentials
- **Network access** from your office/team to EC2 instance (Security Group)

---

## 🎯 Step 1: EC2 Windows Server 2019 Instance Setup

### 1.1 Launch EC2 Instance

```
Recommended specs:
- Instance Type: t3.medium or t3.large
- OS: Windows Server 2019 Base
- Storage: 30 GB (gp2 or gp3)
- Security Group: Allow inbound on port 8501 (TCP)
```

### 1.2 Connect to EC2 Instance

**Option A: Using Remote Desktop Connection (RDC)**

1. Go to AWS EC2 Dashboard
2. Select your instance
3. Click "Connect" → "RDP client"
4. Download Remote Desktop file
5. Open with Remote Desktop Connection
6. Use Administrator credentials from EC2 console
7. Accept certificate warning

**Option B: Using AWS Systems Manager Session Manager**

1. EC2 Dashboard → Instances → Your instance
2. Click "Connect" → "Session Manager"
3. Click "Connect"

---

## 🔧 Step 2: Install Python and Git

### 2.1 Open PowerShell as Administrator

1. Right-click Start menu
2. Select "Windows PowerShell (Admin)"
3. Or use: `Win + X` → `Windows PowerShell (Admin)`

### 2.2 Install Python 3.11

**Using Chocolatey (Recommended):**

```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Python
choco install python -y

# Verify installation
python --version
pip --version

# Upgrade pip
python -m pip install --upgrade pip
```

**Or Manual Installation:**

1. Download Python 3.11 from https://www.python.org/downloads/
2. Run installer
3. ✅ **Important:** Check "Add Python to PATH" during installation
4. Click "Install Now"
5. Wait for completion
6. Verify:
```powershell
python --version
pip --version
```

### 2.3 Install Git

```powershell
# Using Chocolatey
choco install git -y

# Verify installation
git --version

# Or download from https://git-scm.com/download/win
```

---

## 📂 Step 3: Clone Repository

### 3.1 Create Project Directory

```powershell
# Navigate to C: drive
cd C:\

# Create projects directory
mkdir projects
cd projects

# Or your preferred location
```

### 3.2 Clone Repository

```powershell
git clone https://github.com/Jamarapini/aws-rds-inventory-collector.git

cd aws-rds-inventory-collector

# Verify files
dir

# You should see:
# - dashboard.py
# - rds_inventory_collector.py
# - requirements-dashboard.txt
# - .env (create this next)
```

---

## 🔐 Step 4: Configure Database Credentials

### 4.1 Create `.env` File

**Using PowerShell:**

```powershell
# Navigate to project directory
cd C:\projects\aws-rds-inventory-collector

# Create .env file
@"
DB_HOST=ops-prod-ue1-operations-rds-01.cetqu8suvjjy.us-east-1.rds.amazonaws.com
DB_USER=inventory
DB_PASSWORD=V*0>5G^4%2L,ugYI
DB_NAME=inventory
"@ | Out-File -FilePath .env -Encoding UTF8 -NoNewline
```

**Or Using Notepad:**

1. Right-click in folder
2. Select "New" → "Text Document"
3. Name it `.env`
4. Open with Notepad
5. Paste:
```
DB_HOST=ops-prod-ue1-operations-rds-01.cetqu8suvjjy.us-east-1.rds.amazonaws.com
DB_USER=inventory
DB_PASSWORD=V*0>5G^4%2L,ugYI
DB_NAME=inventory
```
6. Save (Ctrl+S)

### 4.2 Verify `.env` File

```powershell
# Check if .env exists and has content
Get-Content .env

# Should show all 4 lines with DB credentials
```

---

## 📦 Step 5: Install Dependencies

### 5.1 Create Virtual Environment

```powershell
# Navigate to project directory
cd C:\projects\aws-rds-inventory-collector

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate again
.\venv\Scripts\Activate.ps1

# You should see (venv) in your prompt
```

### 5.2 Install Required Packages

```powershell
# Make sure venv is activated (should see (venv) in prompt)

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements-dashboard.txt

# This will take 2-3 minutes, be patient

# Verify installations
pip list
```

---

## 🚀 Step 6: Test Dashboard Locally

### 6.1 Run Dashboard

```powershell
# Make sure you're in project directory
cd C:\projects\aws-rds-inventory-collector

# Make sure virtual environment is activated (should see (venv))
# If not, activate it:
.\venv\Scripts\Activate.ps1

# Run the dashboard
streamlit run dashboard.py

# Output should show:
# Streamlit app is running on: http://localhost:8501
```

### 6.2 Access Dashboard

1. Open browser on your Windows machine
2. Go to: `http://localhost:8501`
3. Verify dashboard loads
4. Check all pages work:
   - 📊 Overview
   - 🔍 Instance Browser
   - 📈 Analytics
   - ℹ️ About

### 6.3 Stop Dashboard

```powershell
# Press Ctrl+C in PowerShell to stop
# Or close the PowerShell window
```

---

## 🌐 Step 7: Configure Security Group

**Allow public access to port 8501:**

1. Go to AWS EC2 Dashboard
2. Select your instance
3. Click "Security" tab
4. Click Security Group link
5. Click "Edit inbound rules"
6. Add rule:
   - **Type:** Custom TCP
   - **Port Range:** 8501
   - **Source:** 0.0.0.0/0 (or your company IP)
   - **Description:** Streamlit RDS Dashboard
7. Click "Save rules"

---

## ⚙️ Step 8: Run Dashboard as Windows Service (Auto-Start)

### 8.1 Create Batch Script

**Create file: `C:\projects\aws-rds-inventory-collector\start-dashboard.bat`**

```powershell
# Using PowerShell to create the batch file
@"
@echo off
cd /d C:\projects\aws-rds-inventory-collector
call venv\Scripts\activate.bat
streamlit run dashboard.py
"@ | Out-File -FilePath C:\projects\aws-rds-inventory-collector\start-dashboard.bat -Encoding ASCII
```

### 8.2 Create Windows Service using NSSM

**Option A: Install NSSM (Recommended)**

```powershell
# Open PowerShell as Admin

# Download NSSM
cd C:\temp
Invoke-WebRequest -Uri "https://nssm.cc/download/nssm-2.24-101-g897c7f7.zip" -OutFile nssm.zip

# Extract
Expand-Archive nssm.zip

# Copy to System32
Copy-Item "nssm\nssm-2.24-101-g897c7f7\win64\nssm.exe" "C:\Windows\System32\nssm.exe"

# Verify
nssm --version
```

**Create Service:**

```powershell
# Open PowerShell as Administrator

# Create service
nssm install RDSDashboard C:\projects\aws-rds-inventory-collector\start-dashboard.bat

# Set service to auto-start
nssm set RDSDashboard Start SERVICE_AUTO_START

# Start the service
nssm start RDSDashboard

# Verify it's running
nssm status RDSDashboard

# View service logs
nssm query RDSDashboard
```

**Manage Service:**

```powershell
# Stop service
nssm stop RDSDashboard

# Start service
nssm start RDSDashboard

# Restart service
nssm restart RDSDashboard

# Remove service
nssm remove RDSDashboard confirm
```

### 8.3 Alternative: Using Task Scheduler

**If NSSM doesn't work:**

1. Press `Win + R`, type `taskschd.msc`
2. Click "Create Task..." (right panel)
3. **General Tab:**
   - Name: `RDS Dashboard`
   - ✅ Run with highest privileges
   - ✅ Run whether user is logged in or not

4. **Triggers Tab:**
   - Click "New..."
   - Begin the task: `At startup`
   - Click OK

5. **Actions Tab:**
   - Action: `Start a program`
   - Program: `C:\projects\aws-rds-inventory-collector\start-dashboard.bat`
   - Click OK

6. **Conditions Tab:**
   - Uncheck "Start only if on AC power"
   - Click OK

7. Click "OK" to create task

**Test:**
- Restart Windows Server
- Check if dashboard is running: `http://localhost:8501`

---

## 🔗 Step 9: Get Dashboard URL

### 9.1 Find EC2 Public IP

**Method 1: AWS Console**
1. EC2 Dashboard → Instances
2. Select your instance
3. Copy "Public IPv4 address"

**Method 2: PowerShell**
```powershell
# Run on EC2 instance
Invoke-WebRequest -Uri "http://169.254.169.254/latest/meta-data/public-ipv4" -UseBasicParsing | Select-Object -ExpandProperty Content
```

### 9.2 Share Dashboard URL

```
Dashboard URL: http://YOUR-EC2-PUBLIC-IP:8501

Example: http://54.123.45.67:8501
```

---

## 🧪 Step 10: Verify Dashboard Works

1. Open browser
2. Go to: `http://YOUR-EC2-PUBLIC-IP:8501`
3. Check all pages load:
   - ✅ Overview with charts
   - ✅ Instance Browser with 182 instances
   - ✅ Analytics with visualizations
   - ✅ About page
4. Test filters and export
5. Verify data is current

---

## 🔄 Step 11: Auto-Update Data (Optional)

### 11.1 Schedule Daily Data Refresh

1. Open Task Scheduler (`taskschd.msc`)
2. "Create Task..."
3. **General:**
   - Name: `RDS Inventory Collector`
   - ✅ Run with highest privileges

4. **Triggers:**
   - New → Daily
   - Start: 06:00 AM
   - Recur: Every 1 day
   - Click OK

5. **Actions:**
   - Action: `Start a program`
   - Program: `C:\projects\aws-rds-inventory-collector\venv\Scripts\python.exe`
   - Arguments: `rds_inventory_collector.py --db --all-profiles`
   - Start in: `C:\projects\aws-rds-inventory-collector`
   - Click OK

6. Click "OK" to save

---

## 🛠️ Troubleshooting

### Dashboard won't start

**PowerShell Error - Execution Policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Port 8501 already in use:**
```powershell
# Find process using port 8501
netstat -ano | findstr :8501

# Kill process
taskkill /PID <PID> /F

# Or use different port (edit dashboard.py)
```

### Database connection error

**Verify .env file:**
```powershell
cd C:\projects\aws-rds-inventory-collector
Get-Content .env
```

**Test connection manually:**
```powershell
python -c "import mysql.connector; print('MySQL module OK')"
```

### Python not found

```powershell
# Make sure Python is added to PATH
# Restart PowerShell after installing Python
# Or install again and check "Add Python to PATH"

# Verify:
python --version
pip --version
```

### Security Group blocks port 8501

1. Check EC2 Security Group inbound rules
2. Verify port 8501 is allowed
3. Check Windows Firewall:
```powershell
# Open Windows Defender Firewall with Advanced Security
# Add inbound rule for port 8501
```

---

## 🔒 Security Best Practices

1. **Restrict Security Group** - Use your company IP instead of 0.0.0.0/0
2. **Secure .env file** - Never share or commit to Git
3. **Windows Firewall** - Configure properly for port 8501
4. **Regular Updates** - Update Python and packages monthly
5. **Monitor Service** - Check Task Scheduler logs regularly

---

## 📝 Common Commands

```powershell
# Activate virtual environment
cd C:\projects\aws-rds-inventory-collector
.\venv\Scripts\Activate.ps1

# Deactivate virtual environment
deactivate

# Check running services
Get-Service RDSDashboard

# View system event logs
Get-EventLog -LogName System -Source nssm -Newest 20

# Check port usage
netstat -ano | findstr :8501

# Restart EC2 instance (clean start)
Restart-Computer -Force
```

---

## 📋 Deployment Checklist - Windows Server 2019

- [ ] EC2 Windows Server 2019 instance running
- [ ] Remote Desktop access verified
- [ ] Python 3.11 installed and PATH configured
- [ ] Git installed
- [ ] Repository cloned to C:\projects\aws-rds-inventory-collector
- [ ] Virtual environment created
- [ ] Dependencies installed (requirements-dashboard.txt)
- [ ] `.env` file created with DB credentials
- [ ] Dashboard tested locally (http://localhost:8501)
- [ ] Security Group updated for port 8501
- [ ] Windows Service/Task Scheduler configured
- [ ] Dashboard accessible from team machines
- [ ] All dashboard pages verified working
- [ ] Data refresh scheduled (optional)
- [ ] Documentation shared with team

---

## 🎨 Customization

### Change Port Number

Edit `dashboard.py`:
```python
st.set_page_config(
    page_title="Your Company - RDS Dashboard",
    ...
)
```

Or create `.streamlit/config.toml`:
```toml
[server]
port = 9000
```

### Add Company Logo

1. Upload logo.png to project folder
2. Edit `dashboard.py`:
```python
st.image("logo.png", width=200)
st.title("Your Company - RDS Inventory")
```

---

## 📞 Support

- Check logs in Task Scheduler
- Review this guide
- Check Python/pip versions
- Verify .env file
- Test database connection

---

**Version:** 1.0.0 (Windows Server 2019)  
**Last Updated:** 2026-09-03  
**Author:** DevOps Team
