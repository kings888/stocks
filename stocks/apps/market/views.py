from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.db.models import Q, F, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Stock, TopList, TopListDetail, TraderAnalysis
from stocks.apps.users.views import token_required

@require_http_methods(['GET'])
def stock_list(request):
    stocks = Stock.objects.filter(is_active=True).values('code', 'name', 'market')
    return JsonResponse({'stocks': list(stocks)})

@require_http_methods(['GET'])
def top_list(request):
    date = request.GET.get('date')
    market = request.GET.get('market')
    
    queryset = TopList.objects.select_related('stock')
    if date:
        queryset = queryset.filter(date=date)
    if market:
        queryset = queryset.filter(stock__market=market)
    
    top_lists = queryset.values(
        'id', 'stock__code', 'stock__name', 'date', 'reason',
        'total_buy', 'total_sell', 'net_amount', 'turnover', 'price_change'
    )[:50]
    
    return JsonResponse({'top_lists': list(top_lists)})

@require_http_methods(['GET'])
def top_list_detail(request, top_list_id):
    cache_key = f'top_list_detail_{top_list_id}'
    details = cache.get(cache_key)
    
    if not details:
        details = TopListDetail.objects.filter(top_list_id=top_list_id).values(
            'trader_name', 'trader_type', 'amount', 'proportion'
        )
        details = list(details)
        cache.set(cache_key, details, 300)  # 缓存5分钟
    
    return JsonResponse({'details': details})

@token_required
@require_http_methods(['GET'])
def trader_analysis(request):
    """游资分析接口（仅VIP用户可访问）"""
    if not request.user.is_vip:
        return JsonResponse({'error': '该功能仅对VIP用户开放'}, status=403)
    
    days = int(request.GET.get('days', 30))  # 默认分析最近30天
    min_amount = float(request.GET.get('min_amount', 1000000))  # 默认最小交易额100万
    
    start_date = timezone.now().date() - timedelta(days=days)
    
    # 分析指定时间范围内的游资交易数据
    analysis = TraderAnalysis.objects.filter(
        Q(total_buy_amount__gte=min_amount) | Q(total_sell_amount__gte=min_amount),
        last_updated__gte=start_date
    ).values(
        'trader_name', 'total_buy_amount', 'total_sell_amount',
        'net_amount', 'success_rate', 'appearance_count'
    ).order_by('-appearance_count')[:100]
    
    return JsonResponse({'analysis': list(analysis)})

@token_required
@require_http_methods(['GET'])
def trader_history(request, trader_name):
    """游资历史交易记录（仅VIP用户可访问）"""
    if not request.user.is_vip:
        return JsonResponse({'error': '该功能仅对VIP用户开放'}, status=403)
    
    days = int(request.GET.get('days', 90))  # 默认查询90天历史记录
    start_date = timezone.now().date() - timedelta(days=days)
    
    history = TopListDetail.objects.filter(
        trader_name=trader_name,
        top_list__date__gte=start_date
    ).select_related('top_list', 'top_list__stock').values(
        'top_list__date', 'top_list__stock__code', 'top_list__stock__name',
        'trader_type', 'amount', 'proportion', 'top_list__price_change'
    ).order_by('-top_list__date')
    
    return JsonResponse({'history': list(history)})

@require_http_methods(['GET'])
def market_overview(request):
    """市场资金流向概览"""
    date = request.GET.get('date', timezone.now().date().isoformat())
    
    # 从缓存获取数据
    cache_key = f'market_overview_{date}'
    overview = cache.get(cache_key)
    
    if not overview:
        # 计算当日市场资金流向数据
        daily_stats = TopList.objects.filter(date=date).aggregate(
            total_buy_amount=Sum('total_buy'),
            total_sell_amount=Sum('total_sell'),
            net_amount=Sum('net_amount'),
            avg_turnover=Avg('turnover'),
            stock_count=models.Count('id')
        )
        
        # 按交易所分组统计
        market_stats = TopList.objects.filter(date=date).values(
            'stock__market'
        ).annotate(
            buy_amount=Sum('total_buy'),
            sell_amount=Sum('total_sell'),
            net_flow=Sum('net_amount'),
            stock_count=models.Count('id')
        )
        
        overview = {
            'date': date,
            'daily_stats': daily_stats,
            'market_stats': list(market_stats)
        }
        
        cache.set(cache_key, overview, 3600)  # 缓存1小时
    
    return JsonResponse(overview)