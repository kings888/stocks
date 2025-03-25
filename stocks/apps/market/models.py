from django.db import models
from django.utils import timezone

class Stock(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name='股票代码')
    name = models.CharField(max_length=50, verbose_name='股票名称')
    market = models.CharField(max_length=10, choices=[
        ('SH', '上海'),
        ('SZ', '深圳'),
    ], verbose_name='交易所')
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='最后更新时间')

    class Meta:
        verbose_name = '股票'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['market']),
        ]

    def __str__(self):
        return f'{self.name}({self.code})'

class TopList(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='top_lists', verbose_name='股票')
    date = models.DateField(verbose_name='交易日期')
    reason = models.CharField(max_length=100, verbose_name='上榜原因')
    total_buy = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='买入总额')
    total_sell = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='卖出总额')
    net_amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='净额')
    turnover = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='换手率')
    price_change = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='涨跌幅')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        verbose_name = '龙虎榜'
        verbose_name_plural = verbose_name
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['stock', 'date']),
        ]

    def __str__(self):
        return f'{self.stock.name} - {self.date}'

class TopListDetail(models.Model):
    TRADER_TYPE_CHOICES = [
        ('buy', '买入'),
        ('sell', '卖出'),
    ]

    top_list = models.ForeignKey(TopList, on_delete=models.CASCADE, related_name='details', verbose_name='龙虎榜')
    trader_name = models.CharField(max_length=100, verbose_name='营业部名称')
    trader_type = models.CharField(max_length=4, choices=TRADER_TYPE_CHOICES, verbose_name='交易类型')
    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='交易金额')
    proportion = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='占比')

    class Meta:
        verbose_name = '龙虎榜明细'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['trader_name']),
            models.Index(fields=['trader_type']),
        ]

    def __str__(self):
        return f'{self.top_list.stock.name} - {self.trader_name}'

class TraderAnalysis(models.Model):
    trader_name = models.CharField(max_length=100, unique=True, verbose_name='营业部名称')
    total_buy_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name='总买入金额')
    total_sell_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name='总卖出金额')
    net_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name='净额')
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='成功率')
    appearance_count = models.IntegerField(default=0, verbose_name='上榜次数')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='最后更新时间')

    class Meta:
        verbose_name = '游资分析'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['trader_name']),
            models.Index(fields=['success_rate']),
            models.Index(fields=['appearance_count']),
        ]

    def __str__(self):
        return self.trader_name