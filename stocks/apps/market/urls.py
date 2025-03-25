from django.urls import path
from . import views

urlpatterns = [
    path('stocks/', views.stock_list, name='stock_list'),
    path('top-list/', views.top_list, name='top_list'),
    path('top-list/<int:top_list_id>/detail/', views.top_list_detail, name='top_list_detail'),
    path('trader/analysis/', views.trader_analysis, name='trader_analysis'),
    path('trader/<str:trader_name>/history/', views.trader_history, name='trader_history'),
    path('market/overview/', views.market_overview, name='market_overview'),
]