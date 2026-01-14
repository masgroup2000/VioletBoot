# ⚡ Violet Boot
A high-performance, minimalist USB ISO burner for Linux. A fast alternative to Rufus and Etcher.

##  Features
- **Ultra-Fast:** Written in Python using optimized `dd` logic.
- **Safety-First:** Auto-filters for USB drives to prevent accidental wipes.
- **Modern UI:** Clean, dark themed interface built with CustomTkinter.
- **Lite Weight** only couple Mb in size
🚀 Getting Started
1. Clone the Repo

Bash

git clone https://github.com/YOUR_USERNAME/VioletBoot.git
cd VioletBoot
2. Run the Setup Script This installs system dependencies (Tkinter) and Python libraries automatically.

Bash

chmod +x setup.sh
./setup.sh
3. Launch the App Must be run with root privileges to write to USB hardware:

Bash

sudo python3 VioletBoot.py
🛠 Project Structure
VioletBoot.py: The main application script.

setup.sh: Automated installer for all Linux distros.

requirements.txt: List of Python dependencies.
