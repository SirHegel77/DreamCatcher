import ConfigParser
CONFIG_FILE_PATH = '/opt/dreamcatcher/conf/dreamcatcher.conf'

def read_config():
    config = ConfigParser.SafeConfigParser()
    config.read(CONFIG_FILE_PATH)
    return config
