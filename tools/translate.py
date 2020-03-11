# -*- coding: UTF-8 -*-
from __future__ import division
import sys

sys.path.append("..")
import execjs
import re
import urllib
from json import *
from netvisiter.net_openner import NetOpener


class GGTranslater(object):
    def __init__(self):
        # 初始化网络访问工具
        self.opener = NetOpener("https://translate.google.cn/", "gg_cookie.txt");
        self.opener.init_cookie()
        self.opener.load_cookie()
        self.opener.load_opener()
        # 加载 Google 请求识别标识生成方法
        self.gg_tk_js = execjs.compile("""
            var b = function (a, b) {
                for (var d = 0; d < b.length - 2; d += 3) {
                    var c = b.charAt(d + 2),
                        c = "a" <= c ? c.charCodeAt(0) - 87 : Number(c),
                        c = "+" == b.charAt(d + 1) ? a >>> c : a << c;
                    a = "+" == b.charAt(d) ? a + c & 4294967295 : a ^ c
                }
                return a
            }
            
            var tk =  function (a,TKK) {
                //console.log(a,TKK);
                for (var e = TKK.split("."), h = Number(e[0]) || 0, g = [], d = 0, f = 0; f < a.length; f++) {
                    var c = a.charCodeAt(f);
                    128 > c ? g[d++] = c : (2048 > c ? g[d++] = c >> 6 | 192 : (55296 == (c & 64512) && f + 1 < a.length && 56320 == (a.charCodeAt(f + 1) & 64512) ? (c = 65536 + ((c & 1023) << 10) + (a.charCodeAt(++f) & 1023), g[d++] = c >> 18 | 240, g[d++] = c >> 12 & 63 | 128) : g[d++] = c >> 12 | 224, g[d++] = c >> 6 & 63 | 128), g[d++] = c & 63 | 128)
                }
                a = h;
                for (d = 0; d < g.length; d++) a += g[d], a = b(a, "+-a^+6");
                a = b(a, "+-3^+b+-f");
                a ^= Number(e[1]) || 0;
                0 > a && (a = (a & 2147483647) + 2147483648);
                a %= 1E6;
                return a.toString() + "." + (a ^ h)
            }
        """)
        self.tkk = ""
        self.jsondecoder = JSONDecoder()

    # 获取识别标识生成参数 tkk
    def init_tkk(self):
        page_html = self.opener.visit_url("https://translate.google.cn/", None)
        page_str = page_html.read()
        tkk_str = re.findall(r'TKK=(eval\(\'[^\']*\'\))', page_str)[0]
        tkk_mtd = "".join(["var tkk = function () { return ", tkk_str, "}"])
        tkk_js = execjs.compile(tkk_mtd)
        self.tkk = tkk_js.call("tkk")

    # 生成请求识别标识
    def get_tk(self, source):
        return self.gg_tk_js.call("tk", source, self.tkk)

    # 翻译英文为中文的实现方法，提供给外部调用
    def en_to_zh(self, source):
        self.init_tkk()
        tk = self.get_tk(source)
        params = {"tk": tk, "q": source}
        # 翻译接口连接
        url = "https://translate.google.cn/translate_a/single?client=t&sl=en&tl=zh-CN&hl=zh-CN&dt=at&dt=bd&dt=ex" \
              "&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&ie=UTF-8&oe=UTF-8&otf=1&ssel=0&tsel=0&kc=5" \
              "&" + urllib.urlencode(params)
        # 翻译结果
        rsp = self.opener.visit_url(url, None).read()
        rjson = self.jsondecoder.decode(rsp)
        results = rjson[0]
        rarr = []
        # 解析结果
        for ritem in results:
            ritem_str = ritem[0]
            if ritem_str and ritem_str != "":
                rarr.append(ritem_str.strip().encode("utf-8"))
        return "\n".join(rarr)



if __name__=="__main__":
    ggt = GGTranslater()
    test_html = open("C:\\Users\\Administrator\\Desktop\\spidertemp\\asos\\test.txt", "w")
    test_html.write(ggt.en_to_zh("""
    Jacket by b.Young Wool-mix knit Fluffy finish Funnel neck Button placket Functional pockets Regular fit - true to size  Machine wash 70% Polyester, 30% Wool Our model wears a UK S/EU S/US XS and is 168cm/5'6" tall
    Wool-mix knit 
    Fluffy finish 
    Funnel neck 
    Button placket 
    Functional pockets 
    Regular fit - true to size 
    Machine wash
    70% Polyester, 30% Wool
    Our model wears a UK S/EU S/US XS and is 168cm/5'6" tall
    """))
