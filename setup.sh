 #!/bin/bash


echo "------------------------------------------"
echo "   Violet Boot - Installation Tool"
echo "------------------------------------------"

if [ -f /etc/debian_version ]; then
    echo "[*] Debian/Ubuntu/Mint detected."
    sudo apt update && sudo apt install -y python3-tk python3-pip
elif [ -f /etc/arch-release ]; then
    echo "[*] Arch Linux/Manjaro detected."
    sudo pacman -Sy --noconfirm tk python-pip
elif [ -f /etc/fedora-release ]; then
    echo "[*] Fedora detected."
    sudo dnf install -y python3-tkinter python3-pip
elif [ -f /etc/redhat-release ]; then
    echo "[*] RHEL/CentOS detected."
    sudo yum install -y python3-tkinter python3-pip
else
    echo "[!] OS not fully recognized. Please ensure 'python3-tk' is installed manually."
fi

echo "[*] Installing Python libraries..."
pip3 install customtkinter --break-system-packages || pip3 install customtkinter

echo "[*] Setting executable permissions for Violet Boot..."
chmod +x VioletBoot.py

echo "------------------------------------------"
echo "✅ Setup Complete!"
echo "To launch the app, run:"
echo "   sudo python3 VioletBoot.py"
echo "------------------------------------------"
