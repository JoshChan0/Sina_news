# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymysql import cursors
from twisted.enterprise import adbapi
import logging


# class SinaNewsPipeline:
#     def process_item(self, item, spider):
#         print(f'id:{item["news_id"]} | 标题:{item["news_title"]} ')
#         return item

# 将news数据异步存入mysql数据库中
class ToMysqlDBTwistedPipeline():
    def __init__(self, db_pool):
        self.db_pool = db_pool

    # 从settings中读取参数
    @classmethod
    def from_settings(cls, settings):
        db_params = dict(
            host=settings['MYSQL_HOST'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            port=settings['MYSQL_PORT'],
            database=settings['MYSQL_DBNAME'],
            charset=settings['MYSQL_CHARSET'],
            use_unicode=True,
            # 设置游标类型
            cursorclass=cursors.DictCursor
        )
        # 创建连接池
        db_pool = adbapi.ConnectionPool('pymysql', **db_params)
        # 返回一个pipline对象
        return cls(db_pool)

    # 处理item
    def process_item(self, item, spider):
        # 将要执行的sql放入连接池
        query = self.db_pool.runInteraction(self.insert_into, item)
        # 如果sql执行出现错误，自动回调addErroBack()函数
        query.addErrback(self.handel_error, item, spider)
        logging.info(f'{item["news_id"]}爬取成功')
        return item

    def insert_into(self, cursor, item):
        # sql去重插入，存在相同主键则更新，不存在则插入
        sql = 'insert into sina_news values(%s,%s,%s,%s) on duplicate key update news_id=%s ,news_title=%s ,news_content=%s ,news_date=%s '
        cursor.execute(sql, (
            item['news_id'], item['news_title'], item['news_content'], item['news_date'], item['news_id'],
            item['news_title'], item['news_content'], item['news_date']))

    def handel_error(self, failure, item, spider):
        logging.error(f'{item["news_id"]}插入出错:', failure)
