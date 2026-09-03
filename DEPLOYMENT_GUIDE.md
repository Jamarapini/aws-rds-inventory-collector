# 🚀 AWS RDS Inventory Dashboard - EC2 Deployment Guide

Complete step-by-step guide to deploy the Streamlit dashboard on an EC2 instance for team access.

---

## 📋 Prerequisites

- **EC2 Instance** (Amazon Linux 2 or Ubuntu 20.04+)
- **Python 3.8+** installed
- **Network access** from your office/team to EC2 instance (Security Group)
- **RDS Database** with inventory data already loaded
- **`.env` file** with database credentials

---

## 🎯 Step 1: EC2 Instance Setup

### 1.1 Launch EC2 Instance

```bash
# Recommended specs:
# - Instance Type: t3.medium or t3.small
# - OS: Amazon Linux 2 or Ubuntu 20.04+
# - Storage: 20 GB (gp2)
# - Security Group: Allow inbound on port 8501
```

### 1.2 Connect to EC2 Instance

```bash
# SSH into your instance
ssh -i your-key.pem ec2-user@your-ec2-public-ip

# Or for Ubuntu
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### 1.3 Update System Packages

**For Amazon Linux 2:**
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip git
```

**For Ubuntu:**
```bash
sudo apt update -y
sudo apt install -y python3 python3-pip git
```

---

## 🔧 Step 2: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/Jamarapini/aws-rds-inventory-collector.git

# Navigate to project directory
cd aws-rds-inventory-collector
```

---

## 📦 Step 3: Install Dependencies

### 3.1 Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3.2 Install Required Packages

```bash
# Install dependencies for dashboard
pip install -r requirements-dashboard.txt

# Verify installations
pip list
```

---

## 🔑 Step 4: Configure Database Credentials

### 4.1 Create `.env` File

```bash
# Create .env file in project directory
cat > .env << EOF
DB_HOST=ops-prod-ue1-operations-rds-01.cetqu8suvjjy.us-east-1.rds.amazonaws.com
DB_USER=inventory
DB_PASSWORD=V*0>5G^4%2L,ugYI
DB_NAME=inventory
EOF
```

### 4.2 Verify `.env` File

```bash
# Check contents (be careful with password visibility)
cat .env

# Secure the file
chmod 600 .env
```

---

## 🚀 Step 5: Run Dashboard Locally (Test)

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the dashboard
streamlit run dashboard.py

# Output should show:
# Streamlit app is running on: http://localhost:8501
```

**Test Access:**
- Open browser and navigate to: `http://localhost:8501`
- Verify dashboard loads and data appears

---

## 🌐 Step 6: Configure for Public Access

### 6.1 Update Streamlit Config

```bash
# Create Streamlit config directory
mkdir -p ~/.streamlit

# Create config file
cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[logger]
level = "error"

[client]
showErrorDetails = true
EOF
```

### 6.2 Verify EC2 Security Group

**Important: Configure Security Group to allow traffic**

1. Go to EC2 Dashboard → Instances
2. Select your instance
3. Click "Security" tab → Security Groups
4. Edit inbound rules:
   - **Type:** Custom TCP
   - **Port:** 8501
   - **Source:** `0.0.0.0/0` (or your company IP range)
   - **Description:** Streamlit Dashboard

---

## ⚙️ Step 7: Run Dashboard in Background

### 7.1 Using nohup (Simple)

```bash
# Activate virtual environment
source ~/aws-rds-inventory-collector/venv/bin/activate

# Run in background
cd ~/aws-rds-inventory-collector
nohup streamlit run dashboard.py > dashboard.log 2>&1 &

# Check if running
ps aux | grep streamlit

# View logs
tail -f dashboard.log
```

### 7.2 Using systemd (Recommended - Persistent)

**Create systemd service file:**

```bash
sudo cat > /etc/systemd/system/rds-dashboard.service << EOF
[Unit]
Description=AWS RDS Inventory Dashboard
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/aws-rds-inventory-collector
Environment="PATH=/home/ec2-user/aws-rds-inventory-collector/venv/bin"
ExecStart=/home/ec2-user/aws-rds-inventory-collector/venv/bin/streamlit run dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

**For Ubuntu, use `ubuntu` instead of `ec2-user`**

**Enable and start service:**

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable rds-dashboard

# Start the service
sudo systemctl start rds-dashboard

# Check status
sudo systemctl status rds-dashboard

# View logs
sudo journalctl -u rds-dashboard -f
```

**Useful commands:**

```bash
# Stop dashboard
sudo systemctl stop rds-dashboard

# Restart dashboard
sudo systemctl restart rds-dashboard

# Check if running
sudo systemctl is-active rds-dashboard

# View recent logs
sudo journalctl -u rds-dashboard -n 50
```

---

## 🔗 Step 8: Access Dashboard from Team

### 8.1 Get Your EC2 Public IP

```bash
# From EC2 instance
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Or from AWS Console
# EC2 Dashboard → Instances → Your Instance → Public IPv4 address
```

### 8.2 Share Access URL

```
Dashboard URL: http://YOUR-EC2-PUBLIC-IP:8501
```

**Example:**
```
http://54.123.45.67:8501
```

---

## 📊 Step 9: Verify Dashboard is Working

1. **Open browser:** `http://YOUR-EC2-PUBLIC-IP:8501`
2. **Check pages:**
   - ✅ Overview page loads with charts
   - ✅ Instance Browser shows 182 RDS instances
   - ✅ Analytics page displays data
   - ✅ Filters work correctly
   - ✅ Export CSV works

---

## 🔄 Step 10: Auto-Refresh Data (Optional)

To automatically refresh RDS inventory data daily:

### 10.1 Create Cron Job

```bash
# Edit crontab
crontab -e

# Add this line (runs collection at 6 AM daily)
0 6 * * * cd /home/ec2-user/aws-rds-inventory-collector && source venv/bin/activate && python3 rds_inventory_collector.py --db --all-profiles >> /tmp/rds_collector.log 2>&1
```

---

## 🛠️ Troubleshooting

### Dashboard won't start

```bash
# Check if port 8501 is in use
sudo lsof -i :8501

# Kill process on port 8501
sudo kill -9 <PID>

# Check logs
sudo journalctl -u rds-dashboard -n 100
```

### Database connection error

```bash
# Verify .env file exists and is correct
cat ~/.env

# Test database connection
python3 -c "import os; os.chdir('/home/ec2-user/aws-rds-inventory-collector'); from dashboard import get_db_connection; get_db_connection()"
```

### Port 8501 blocked

```bash
# Check if port is open
curl http://localhost:8501

# Verify Security Group allows port 8501
# EC2 Dashboard → Security Groups → Edit Inbound Rules
```

### Out of Memory

```bash
# Increase swap (if needed)
sudo dd if=/dev/zero of=/swapfile bs=1G count=2
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📝 Maintenance

### Update Dashboard Code

```bash
# Navigate to project
cd ~/aws-rds-inventory-collector

# Pull latest changes
git pull origin main

# Restart service
sudo systemctl restart rds-dashboard
```

### Backup .env File

```bash
# Create backup (keep secure)
cp .env .env.backup
chmod 600 .env.backup

# Store safely (never commit to git)
```

---

## 🔒 Security Best Practices

1. **Restrict Security Group** - Only allow your company IP range (not 0.0.0.0/0)
2. **Use HTTPS** - Consider adding Nginx reverse proxy with SSL
3. **Secure .env** - Never commit to Git, use `chmod 600`
4. **Update regularly** - Run `git pull` and `pip install -r requirements-dashboard.txt` periodically
5. **Monitor logs** - Regularly check `sudo journalctl -u rds-dashboard`

---

## 🎨 Customization

### Change Colors/Theme

Edit `dashboard.py` and modify the CSS section:

```python
st.markdown("""
    <style>
    .main {
        background-color: #your-color;
    }
    </style>
    """, unsafe_allow_html=True)
```

### Add Team Logo

Add this to the top of `dashboard.py`:

```python
st.image("path-to-logo.png", width=200)
```

### Change Page Title

Edit in `dashboard.py`:

```python
st.set_page_config(
    page_title="Your Company - RDS Dashboard",
    page_icon="🏢",
    ...
)
```

---

## 📞 Support

For issues or questions:
1. Check logs: `sudo journalctl -u rds-dashboard -f`
2. Review this guide
3. Check GitHub Issues: https://github.com/Jamarapini/aws-rds-inventory-collector

---

## 📋 Checklist - Deployment Steps

- [ ] EC2 instance launched and running
- [ ] SSH access verified
- [ ] Python 3 and pip installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file created with DB credentials
- [ ] Dashboard tested locally
- [ ] Streamlit config created
- [ ] Security Group updated for port 8501
- [ ] systemd service created and enabled
- [ ] Dashboard accessible from team machines
- [ ] All pages and features verified working
- [ ] Cron job configured for daily data refresh (optional)

---

**Version:** 1.0.0  
**Last Updated:** 2026-09-03  
**Author:** DevOps Team
