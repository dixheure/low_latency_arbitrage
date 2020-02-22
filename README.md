# low_latency_arbitrage


On Linux, tape the following command. 

taskset -c 0 python low_latency_arbitrage.py

It will dedicat core 0 (CPU) to run low_latency_arbitrage.py. You can tape 'top' in terminal then push button 1 in order to see core consuming

If you would more performance, you could overclock your CPU, RAM in the BIOS (or proprietary tool)

BE AWARE it lower considerably the lifespan of your hardware  

