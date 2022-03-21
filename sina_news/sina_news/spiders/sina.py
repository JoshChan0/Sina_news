import scrapy
import time
from sina_news.items import SinaNewsItem
import logging
import re


class SinaSpider(scrapy.Spider):
    name = 'sina'
    # allowed_domains = ['news.sina.com.cn']
    # 设置需要爬取的新闻的日期，该网站的api设置了由当日8点时间戳生成的参数，必须有该参数才能获取到当天的新闻标题分页
    str_datetime_list = ['2022-03-21 08:00:00', '2022-03-20 08:00:00','2022-03-19 08:00:00','2022-03-18 08:00:00']
    # 初始化api
    init_url = f'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=50&callback=jQuery111208082088770025779_1646841761904&page='
    # 起始页
    startpage = 1
    # 终止页，每一天的新闻只能显示50页，每一页有50条新闻，一天能显示新闻量是2500
    endpage = 50

    # 基于datetime和page构造新闻标题页api
    def make_url(self, str_datetime, page):
        # 根据str_datetime来制成需要的时间戳
        datetimestamp = time.mktime(time.strptime(str_datetime, '%Y-%m-%d %H:%M:%S'))
        # 将时间戳换算成该网站的格式ntime，计算必要的time参数
        ntime = int(datetimestamp * 1000 - 1000 * 60 * 60 * 8)

        # etime stime ctime三个参数需要弄上api上
        etime = str(int(ntime / 1000))
        stime = str(int((ntime + 1000 * 60 * 60 * 24) / 1000))
        ctime = stime
        # 拼接成最终的url
        url = self.init_url + str(page) + '&etime=' + etime + '&stime=' + stime + '&ctime=' + ctime
        print('url=', url)
        return url

    # scrapy从此处开始
    def start_requests(self):
        for str_datetime in self.str_datetime_list:
            date = str_datetime.strip(' ')[0]
            logging.info(f'开始爬取{date}的新闻')
            for page in range(self.startpage, self.endpage):
                # 构造新闻标题页api
                url = self.make_url(str_datetime, page)
                # 对新闻标题分页进行爬取解析
                yield scrapy.Request(url, callback=self.parse, meta={'date': date, 'page': page})

    # 对新闻标题分页进行解析
    def parse(self, response):
        date = response.meta['date']
        page = response.meta['page']

        response.text
        # 返回的是js格式的text，利用正则匹配出每一页的所有新闻详情页url
        urls = re.findall('"url":"(.*?)"', response.text, re.S)
        news_url_list = []
        for detail_url in urls:
            # 对获取到的url进行格式设置
            detail_url = re.sub(r'\\', '', detail_url)
            news_url_list.append(detail_url)
        logging.info(f'爬取第{date}天新闻的第{page}页面成功！')
        # print(news_url_list)
        for news_url in news_url_list:
            # 对新闻详情页面进行爬取解析
            yield scrapy.Request(news_url, callback=self.parse_detail)

    # 对新闻详情页面进行解析
    def parse_detail(self, response):
        item = SinaNewsItem()
        # 解析新闻的id
        item['news_id'] = re.search(r'\d+', response.url.split('/')[-1]).group()
        # 解析新闻的标题
        item['news_title'] = response.xpath('//h1[@class="main-title"]/text()').extract_first()
        # 解析新闻的内容，xpath匹配出的是每个p标签下的文本，需要进行修改，转为字符串
        article_p_list = response.xpath('//div[@class="article"]//p//text()').extract()
        article_list = []
        for p in article_p_list:
            p = p.replace('\u3000', '').strip()
            article_list.append(p)
        # 修改后的新闻内容
        article = '/'.join(article_list)
        item['news_content'] = article
        # 新闻发布的日期时间
        item['news_date'] = response.xpath('//span[@class="date"]/text()').extract_first()
        yield item
