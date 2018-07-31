import logging

import requests

import scrapy
from ooxx.items import ooxxItem
from scrapy import Request

logger=logging.getLogger(__name__)

class ooxx(scrapy.Spider):
    name='ooxx'
    #域中不需要添加http：//否则域会变成网址（urls）
    #域以外的网址会被过滤掉
    allowed_domains=['ip.chinaz.com']
    def start_requests(self):
        url = 'http://ip.chinaz.com/getip.aspx'
        for _ in range(3):
            yield Request(url=url, meta={'Firefox': True}, callback=self.parse, dont_filter=True)

    def parse(self,response):
        #查询ip的网站
        #高匿代理：不改变客户机请求+隐藏客户的真实ip
        #普通匿名代理：改变客户的请求+隐藏客户的真实ip（被访问的网站虽然不知道你的ip地址，但能侦测ip的网页仍然可以查到你的ip）
        #透明代理：改变客户的请求+传送客户的真实ip
        logger.info(response.text)
