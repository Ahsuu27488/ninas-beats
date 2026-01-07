#!/data/data/com.termux/files/usr/bin/bash
# Nina's Beats - One-Click Installer
# She runs: bash install.sh

echo "♥"
echo "♥ Setting up Nina's Beats..."
echo "♥"

# Wait a moment for dramatic effect
sleep 1

# Update and install dependencies
echo "♥ Getting things ready..."
pkg update -y >/dev/null 2>&1
pkg install -y mpv python >/dev/null 2>&1

# Install Python packages
echo "♥ Installing magic..."
pip install rich >/dev/null 2>&1

# Configure auto-start on Termux launch
echo "♥ Setting up to start automatically..."
cat > ~/.bashrc << 'EOF'
# Auto-start Nina's Beats
python ~/ninas-beats/src/main.py

# After exit, normal shell
export PS1="♥ "
EOF

echo ""
echo "✓ Done! Close Termux and reopen it..."
echo "✓ The magic will start automatically ♥"
echo ""
sleep 2
exec bash
