# Wake Nassy

A simple web application that allows you to wake up your NAS (Network Attached Storage) device using Wake-on-LAN. The application provides a clean, mobile-friendly interface with real-time status monitoring.

## Requirements

- Python 3.x
- Flask
- Flask-BasicAuth
- Gunicorn
- wakeonlan utility

## Installation

1. Clone the repository:
```bash
git clone git@github.com:stefanbesler/wake-nassy.git
cd wake-nassy
```

2. Install the required Python packages:
```bash
pip install flask flask-basicauth gunicorn
```

3. Install the wakeonlan utility:
```bash
# On Debian/Ubuntu
sudo apt-get install wakeonlan

# On Arch Linux
sudo pacman -S wakeonlan
```

4. Configure the application:
   - Update the following variables in `wake-nassy.py`:
     - `NAS_MAC_ADDRESS`: Your NAS's MAC address
     - `NAS_IP`: Your NAS's IP address
     - `USERNAME`: Basic auth username
     - `PASSWORD`: Basic auth password

## Running the Application

### Manual Start

To start the application manually:

```bash
python wake-nassy.py
```

### Automatic Start with HTTPS

To run the application with HTTPS support using Gunicorn, add the following line to your crontab (`crontab -e`):

```bash
@reboot gunicorn -b 0.0.0.0:2183 \
wake-nassy:app \
--certfile=/path/to/cert.pem --keyfile=/path/to/privkey.pem \
--chdir=/path/to/wake-nassy >> /path/to/logs/wake-nassy.log 2>&1
```

Replace the following paths with your actual paths:
- `/path/to/cert.pem`: Path to your SSL certificate
- `/path/to/privkey.pem`: Path to your SSL private key
- `/path/to/wake-nassy`: Path to the application directory
- `/path/to/logs/wake-nassy.log`: Path to the log file

## Security Notes

- The application uses basic authentication to protect the wake functionality
- HTTPS is recommended for secure communication
- Keep your SSL certificates and private keys secure
- Regularly update your credentials


