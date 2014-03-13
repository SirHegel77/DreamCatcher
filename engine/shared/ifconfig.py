from process import Process

def ifconfig():
    command = ['/sbin/ifconfig', '-a']
    result = {}
    with Process(command) as p:
        name = None
        for line in p:
            if name == None:
                name = line[0:10].strip()
            if len(line.strip()) == 0:
                name = None
            if name:
                if 'inet addr' in line:
                    values = line.strip().split(':')
                    ip = values[1].split()[0]
                    result[name] = ip
                    name = None
    return result


if __name__ == "__main__":
    result = ipconfig()
    print result
