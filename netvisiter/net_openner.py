# -*- coding: UTF-8 -*-
import urllib
import urllib2
import cookielib


class NetOpener(object):
    def __init__(self, host, cookie_fname):
        # 配置cookie信息，cookie文件路径根据自己需要配置
        self.cookie_dir = "".join(["C:\\Users\\Administrator\\Desktop\\spidertemp\\cookies\\", cookie_fname])
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "Origin": host,
            "Referer": host
        }
        self.host = host
        self.cookie = None
        self.opener = None

    # 初始化cookie
    def init_cookie(self):
        cookie = cookielib.MozillaCookieJar(self.cookie_dir)
        handler = urllib2.HTTPCookieProcessor(cookie)
        opener = urllib2.build_opener(handler)
        opener.addheaders.append(['Cookie', 'c=c'])
        lureq = self.create_request(self.host, None)
        opener.open(lureq)
        cookie.save(ignore_discard=True, ignore_expires=True)

    # 加载cookie
    def load_cookie(self):
        self.cookie = cookielib.MozillaCookieJar().load(self.cookie_dir, ignore_discard=True, ignore_expires=True)

    # 设置cookie
    def set_cookie(self, key_values):
        self.opener.addheaders.append(['Cookie', key_values])

    # 加载opener
    def load_opener(self):
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie))

    # 创建网络请求
    def create_request(self, url, params):
        data = None
        if params is not None:
            data = urllib.urlencode(params)
        request = urllib2.Request(url, data, self.headers)
        return request

    # 访问url
    def visit_url(self, url, params):
        return self.opener.open(self.create_request(url, params))
