# Laser Train
---
This code uses RL to train the modulator to generate as short laser impuse as possible. For now, I am not sure what we are doing, so more description will appear here soon.

## Folder structure:
- `laser`: Everything that happens on the laser side. It includes:
	 - code by **Alicja Kwaśny** for  communication with devices
	 - a simple lients that queries the server and ask which funcion should be executed
- `laser_train`: main folder of the repo, that contains the environment and (....) we will see :>. For now, we have
	- `server.py` A simple, flask server used to test the communication with the laser
	- `gym_server.py` - A server, wrapped up in a gymnasium environment
	- `tools.py` - various tools, currently mainly to handle config.yaml files


