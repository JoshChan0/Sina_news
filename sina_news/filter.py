import pymysql
connect = pymysql.connect(host="rm-7xv4tx3319797f1d34o.mysql.rds.aliyuncs.com", port=3306, user="chen", passwd="Cjx97625*", charset="utf8",
                          db="spider_test")
cursor = connect.cursor()

try:
    #统计空值数据行数
    sql1='select count(news_id) from sina_news where news_title is null or news_content is null or news_date is null'
    cursor.execute(sql1)
    result = cursor.fetchone()
    #删除空值数据
    del_sql1='delete from sina_news where news_title is null or news_content is null or news_date is null'
    cursor.execute(del_sql1)
    connect.commit()
    print(f'已删除{result[0]}条空数据')
except Exception as e:
    connect.rollback()
    print('错误:',e)


try:
    #统计无效数据
    sql2 = 'select count(news_id) from sina_news where length(news_content)<150'
    cursor.execute(sql2)
    result=cursor.fetchone()
    #删除无效数据
    del_sql2='delete from sina_news where length(news_content)<150'
    cursor.execute(del_sql2)
    connect.commit()
    print(f'已删除{result[0]}条内容无效数据')
except Exception as e:
    connect.rollback()
    print('错误:',e)


cursor.close()
connect.close()
print('数据库已关闭')
