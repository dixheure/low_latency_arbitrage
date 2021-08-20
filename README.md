# low_latency_arbitrage

On Linux, type the following command. 

taskset -c 0 python low_latency_arbitrage.py

It will dedicat core 0 (CPU) to run low_latency_arbitrage.py. You can type 'top' in terminal, then push button '1' in order to see core consuming process.

If you would more performance, you could overclock your CPU, RAM in the BIOS (or proprietary tool)

BE AWARE you should master that step, it lower considerably the lifespan of your hardware  

