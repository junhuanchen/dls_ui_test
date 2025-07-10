mpfs -o com13 -c "put gocan.py"

mpfs -o com26 -c "rf gocan_player.py"

mpfs -o com13 -c "put gocan.py; rf gocan_player.py"
