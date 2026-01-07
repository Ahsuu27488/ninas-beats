#!/data/data/com.termux/files/usr/bin/bash
# Nina's Beats - One-Click Installer

echo "♥"
echo "♥ Setting up Nina's Beats..."
echo "♥"

sleep 1

# Update and install dependencies
echo "♥ Getting things ready..."
pkg update -y >/dev/null 2>&1
pkg install -y mpv python >/dev/null 2>&1

# Install Python packages
echo "♥ Installing magic..."
pip install rich >/dev/null 2>&1

# Add simple 'beats' command - run as module to fix import errors
echo "♥ Almost done..."
cat >> ~/.bashrc << 'EOF'

# Nina's Beats - type 'beats' to start
alias beats="cd ~/ninas-beats/src && python -m ninas_beats"
EOF

echo ""
echo "✓ Setup complete!"
echo "✓ Close Termux and reopen it..."
echo "✓ Then type: beats"
echo ""
echo "♥"
sleep 2
