#!/bin/bash

echo "🛡️  Starting NeuralTrap System...
echo "=================================================="

# Start MariaDB
echo "Starting database..."
sudo systemctl start mariadb

# Start Cowrie
echo "Starting honeypot..."
cd ~/cowrie
source cowrie-env/bin/activate
cowrie start
sleep 3

# Start Ollama
echo "Starting LLM..."
sudo systemctl start ollama
sleep 2

# Start Dashboard in background
echo "Starting dashboard..."
cd ~/cowrie
source cowrie-env/bin/activate
streamlit run dashboard.py --server.port 8501 &
sleep 3

echo ""
echo "✅ Database running"
echo "✅ Honeypot running on port 2222"
echo "✅ LLM running"
echo "✅ Dashboard running on http://localhost:8501"
echo ""
echo "Starting NeuralTrap main engine..."
echo "=================================================="

# Start main NeuralTrap engine (runs in foreground)
cd ~/cowrie
source cowrie-env/bin/activate
python3 neuraltrap.py
