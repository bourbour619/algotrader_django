from django.urls import path
from .views import *


urlpatterns = [
    path('', index, name='index'),
    path('bourse/', bourse_backtest, name='bourse_backtest'),
    path('crypto/', crypto_backtest, name='crypto_backtest'),
    path('bourse/tickers/', ajax_bourse_tikcers, name='ajax_bourse_tikcers')
]