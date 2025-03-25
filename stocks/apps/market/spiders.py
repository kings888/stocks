import scrapy
from scrapy.crawler import CrawlerProcess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from .models import Stock, TopList, TopListDetail, TraderAnalysis

class TopListSpider(scrapy.Spider):
    name = 'toplist'
    allowed_domains = ['eastmoney.com']
    
    def start_requests(self):
        # 东方财富龙虎榜数据URL
        url = 'http://data.eastmoney.com/stock/tradedetail.html'
        yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        # 使用Selenium处理动态加载的数据
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        
        try:
            driver.get(response.url)
            # 等待数据加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'table-list-tbody'))
            )
            
            # 解析龙虎榜数据
            rows = driver.find_elements(By.CSS_SELECTOR, '.table-list-tbody tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) < 10:
                    continue
                
                # 提取股票信息
                stock_code = cells[1].text.strip()
                stock_name = cells[2].text.strip()
                market = 'SH' if stock_code.startswith('6') else 'SZ'
                
                # 保存或更新股票信息
                stock, _ = Stock.objects.get_or_create(
                    code=stock_code,
                    defaults={
                        'name': stock_name,
                        'market': market
                    }
                )
                
                # 解析交易数据
                date_str = cells[0].text.strip()
                trade_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                reason = cells[3].text.strip()
                price_change = float(cells[4].text.strip().rstrip('%'))
                turnover = float(cells[5].text.strip().rstrip('%'))
                total_buy = float(cells[6].text.strip()) * 10000
                total_sell = float(cells[7].text.strip()) * 10000
                net_amount = total_buy - total_sell
                
                # 保存龙虎榜数据
                top_list = TopList.objects.create(
                    stock=stock,
                    date=trade_date,
                    reason=reason,
                    total_buy=total_buy,
                    total_sell=total_sell,
                    net_amount=net_amount,
                    turnover=turnover,
                    price_change=price_change
                )
                
                # 获取交易明细
                detail_link = cells[9].find_element(By.TAG_NAME, 'a')
                detail_link.click()
                
                # 等待明细数据加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'detail-table'))
                )
                
                # 解析买入明细
                buy_rows = driver.find_elements(By.CSS_SELECTOR, '.detail-table:nth-child(1) tr')
                for buy_row in buy_rows[1:]:
                    buy_cells = buy_row.find_elements(By.TAG_NAME, 'td')
                    if len(buy_cells) < 3:
                        continue
                    
                    trader_name = buy_cells[0].text.strip()
                    amount = float(buy_cells[1].text.strip()) * 10000
                    proportion = float(buy_cells[2].text.strip().rstrip('%'))
                    
                    TopListDetail.objects.create(
                        top_list=top_list,
                        trader_name=trader_name,
                        trader_type='buy',
                        amount=amount,
                        proportion=proportion
                    )
                
                # 解析卖出明细
                sell_rows = driver.find_elements(By.CSS_SELECTOR, '.detail-table:nth-child(2) tr')
                for sell_row in sell_rows[1:]:
                    sell_cells = sell_row.find_elements(By.TAG_NAME, 'td')
                    if len(sell_cells) < 3:
                        continue
                    
                    trader_name = sell_cells[0].text.strip()
                    amount = float(sell_cells[1].text.strip()) * 10000
                    proportion = float(sell_cells[2].text.strip().rstrip('%'))
                    
                    TopListDetail.objects.create(
                        top_list=top_list,
                        trader_name=trader_name,
                        trader_type='sell',
                        amount=amount,
                        proportion=proportion
                    )
                
                # 返回主列表
                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'table-list-tbody'))
                )
        
        finally:
            driver.quit()

@shared_task
def crawl_toplist_data():
    """定时爬取龙虎榜数据的Celery任务"""
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    process.crawl(TopListSpider)
    process.start()

@shared_task
def update_trader_analysis():
    """更新游资交易数据分析的Celery任务"""
    # 获取最近90天的数据进行分析
    start_date = timezone.now().date() - timedelta(days=90)
    
    # 获取所有交易员的交易记录
    traders = TopListDetail.objects.values('trader_name').distinct()
    
    for trader in traders:
        trader_name = trader['trader_name']
        
        # 统计交易数据
        buy_stats = TopListDetail.objects.filter(
            trader_name=trader_name,
            trader_type='buy',
            top_list__date__gte=start_date
        ).aggregate(
            total_amount=models.Sum('amount'),
            count=models.Count('id')
        )
        
        sell_stats = TopListDetail.objects.filter(
            trader_name=trader_name,
            trader_type='sell',
            top_list__date__gte=start_date
        ).aggregate(
            total_amount=models.Sum('amount'),
            count=models.Count('id')
        )
        
        # 计算成功率（以上涨为成功）
        success_count = TopListDetail.objects.filter(
            trader_name=trader_name,
            top_list__date__gte=start_date,
            top_list__price_change__gt=0
        ).count()
        
        total_count = TopListDetail.objects.filter(
            trader_name=trader_name,
            top_list__date__gte=start_date
        ).count()
        
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        # 更新或创建分析记录
        TraderAnalysis.objects.update_or_create(
            trader_name=trader_name,
            defaults={
                'total_buy_amount': buy_stats['total_amount'] or 0,
                'total_sell_amount': sell_stats['total_amount'] or 0,
                'net_amount': (buy_stats['total_amount'] or 0) - (sell_stats['total_amount'] or 0),
                'success_rate': success_rate,
                'appearance_count': total_count
            }
        )