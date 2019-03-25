import os
import time

def measure_temp():
        gpu = os.popen("vcgencmd measure_temp").readline().rstrip()
        print(gpu.replace("temp=","GPU: "))
        cpu = float(os.popen("cat /sys/class/thermal/thermal_zone0/temp").readline())/1000.0
        print("CPU: "+str(cpu)+'C')

while True:
        measure_temp()
        time.sleep(1)
