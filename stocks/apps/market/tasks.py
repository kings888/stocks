from celery import shared_task
from celery.schedules import crontab
from django.conf import settings
from django.core.cache import cache
from .spiders import crawl_toplist_data, update_trader_analysis

# 注册Celery定时任务
@shared_task
def schedule_crawl_toplist():
    """每个交易日15:30后爬取当日龙虎榜数据"""
    crawl_toplist_data()

@shared_task
def schedule_update_analysis():
    """每天凌晨更新游资交易数据分析"""
    update_trader_analysis()

# 配置定时任务
app.conf.beat_schedule = {
    'crawl-toplist-data': {
        'task': 'stocks.apps.market.tasks.schedule_crawl_toplist',
        'schedule': crontab(hour=15, minute=30, day_of_week='1-5'),  # 每个工作日15:30执行
    },
    'update-trader-analysis': {
        'task': 'stocks.apps.market.tasks.schedule_update_analysis',
        'schedule': crontab(hour=0, minute=30),  # 每天0:30执行
    },
}