import os
from configparser import ConfigParser


class Dictionary(dict):
    """

    把settings.ini中的参数添加值dict

    """

    def __getattr__(self, keyname):
        # 如果key值不存在则返回默认值"not find config keyname"
        return self.get(keyname, "settings.ini中没有找到对应的keyname")


class Conf:
    """
    ConfigParser二次封装，在字典中获取value
    """

    def __init__(self):
        # 设置conf.ini路径
        current_dir = os.path.dirname(__file__)
        top_one_dir = os.path.dirname(current_dir)
        file_name = top_one_dir + "/settings.ini"
        # 实例化ConfigParser对象
        self.config = ConfigParser()
        self.config.read(file_name)
        # 根据section把key、value写入字典
        for section in self.config.sections():
            setattr(self, section, Dictionary())
            for keyname, value in self.config.items(section):
                setattr(getattr(self, section), keyname, value)

    def getconf(self, section):
        """配置文件读取

        读取ini文件
        用法：
        conf = Conf()
        info = conf.getconf("main").url

        Args:
            section (str): ini中的section名

        Returns:
            object: getattr()函数

        """
        if section in self.config.sections():
            pass
        else:
            print("config.ini 找不到该 section")
        return getattr(self, section)
