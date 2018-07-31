import logging
import random
import sys
import time

from lxml import etree
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from twisted.internet.error import (ConnectError, ConnectionLost,
                                    ConnectionRefusedError, TCPTimedOutError,
                                    TimeoutError)
from twisted.web._newclient import ResponseNeverReceived
sys.path.append(r'C:\Users\Administrator\Desktop\proxy_pool\ooxx')
import fetch_free_proxies



logger=logging.getLogger(__name__)

class ooxxSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

class HttpProxyMiddleware(object):
        #遇到这些类型的错误不再传给retry
        
        DONT_RETRY_ERRORS=(TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError, ConnectionLost, TCPTimedOutError, ValueError)
        
        def __init__(self):
            #初始化代理列表
            #self.proxies=[{'proxy':None,'valid':True, 'count':0}] 此方法将自己搭建的可信代理和不使用代理加入初始代理列表
            #全部采用代理ip
            self.proxies=[]
            #将无法访问此网页的代理保存在无效代理列表中，而不是删除，这样可以避免在获取新的代理时将这些无效代理再次加入代理列表
            self.invalid_proxies=[]
            proxy_list=fetch_free_proxies.fetch_xicidaili_proxies()
            for proxy in proxy_list:
                self.proxies.append(proxy)

        def process_request(self, request, spider):
            self.get_proxy(request)
            #固定格式：request.meta['proxy']=代理ip 

        def process_response(self, request, response, spider):
            # status不是正常的200而且不在spider声明的正常爬取过程中可能出现的
            #\表示代码换行
            if response.status != 200 \
                and (not hasattr(spider, 'website_possible_httpstatus_list') \
                or response.status not in spider.website_possible_httpstatus_list):
                self.invalid_proxies.append(self.proxies[0])  
                del self.proxies[0]
                #reqeust为什么要copy？
                new_request=request.copy()
                return new_request
            else:
                return response

        def process_exception(self,request,exception,spider):
            #处理使用代理时出现的异常
            if isinstance(exception, self.DONT_RETRY_ERRORS):
                self.invalid_proxies.append(self.proxies[0])  
                del self.proxies[0]
                new_request=request.copy()
                return new_request

        def get_proxy(self,request):
            if len(self.proxies)<2:
                self.fetch_new_proxies()
            request.meta['proxy']=self.proxies[0]

        def fetch_new_proxies(self):
            #抓取新的代理添加到代理列表中
            count=0
            new_proxy_list=fetch_free_proxies.fetch_free_proxies()
            for new_proxy in new_proxy_list:
                if new_proxy not in (self.proxies or self.invalid_proxies):
                    self.proxies.append(new_proxy)
            if  len(self.proxies)<2:
                logger.debug('暂停5分钟后再次抓取代理')
                time.sleep(300)
                count+=1
                #连续暂停两个五分钟后直接退出
                assert count==2
                self.fetch_new_proxies()

class SeleniumMiddleware(object):
    @classmethod
    def process_request(cls, request, spider):
        if 'Firefox' in request.meta:
            logger.info('正在使用无头浏览器')
            #采用的是代理ip 
            if 'proxy' in request.meta:
                logger.info(request.meta['proxy'])
            options = Options()
            options.add_argument('-headless')  
            driver=webdriver.Firefox(executable_path=r'D:\Program Files (x86)\Mozilla Firefox\geckodriver',firefox_options=options)
            driver.get(request.url)
            #页面渲染可能较慢，尤其是在网速较差的时候，所以需要暂停一段时间
            driver.implicitly_wait(20)
            content = driver.page_source
            driver.quit()  
            return HtmlResponse(request.url, encoding='utf-8', body=content, request=request)
        else:
            return None
