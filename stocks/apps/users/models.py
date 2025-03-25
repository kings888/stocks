from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    phone = models.CharField(max_length=11, blank=True, null=True, verbose_name='手机号')
    is_vip = models.BooleanField(default=False, verbose_name='是否是VIP用户')
    vip_expire_time = models.DateTimeField(null=True, blank=True, verbose_name='VIP过期时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

class Subscription(models.Model):
    SUBSCRIPTION_TYPES = [
        ('monthly', '月度会员'),
        ('quarterly', '季度会员'),
        ('yearly', '年度会员'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', verbose_name='用户')
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_TYPES, verbose_name='订阅类型')
    start_date = models.DateTimeField(default=timezone.now, verbose_name='开始时间')
    end_date = models.DateTimeField(verbose_name='结束时间')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='支付金额')
    payment_id = models.CharField(max_length=100, verbose_name='支付订单号')
    is_active = models.BooleanField(default=True, verbose_name='是否有效')

    class Meta:
        verbose_name = '订阅记录'
        verbose_name_plural = verbose_name
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.user.username} - {self.get_subscription_type_display()}'