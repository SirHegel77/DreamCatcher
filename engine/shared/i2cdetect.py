import os

def i2cdetect():
    result = os.popen('/usr/sbin/i2cdetect -y 1').read()
    for line in result.split('\n')[1:]:
        columns = [line[i:i+2] for i in range(0, len(line), 2)]
        print columns
