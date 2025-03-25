from django.contrib.auth import authenticate
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import jwt
from datetime import datetime, timedelta
from .models import User, Subscription
from django.conf import settings

def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION_DELTA)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def token_required(view_func):
    def wrapper(request, *args, **kwargs):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        if not token:
            return JsonResponse({'error': '未提供认证令牌'}, status=401)
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user = User.objects.get(id=payload['user_id'])
            request.user = user
            return view_func(request, *args, **kwargs)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return JsonResponse({'error': '无效或过期的令牌'}, status=401)
    return wrapper

@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    try:
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': '用户名已存在'}, status=400)
        
        user = User.objects.create_user(
            username=username,
            password=password,
            phone=phone
        )
        token = generate_token(user)
        return JsonResponse({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'is_vip': user.is_vip
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    user = authenticate(username=username, password=password)
    if not user:
        return JsonResponse({'error': '用户名或密码错误'}, status=401)
    
    token = generate_token(user)
    return JsonResponse({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'is_vip': user.is_vip,
            'vip_expire_time': user.vip_expire_time.isoformat() if user.vip_expire_time else None
        }
    })

@token_required
@require_http_methods(['POST'])
def subscribe(request):
    subscription_type = request.POST.get('subscription_type')
    payment_id = request.POST.get('payment_id')
    
    if subscription_type not in dict(Subscription.SUBSCRIPTION_TYPES):
        return JsonResponse({'error': '无效的订阅类型'}, status=400)
    
    duration_days = {
        'monthly': 30,
        'quarterly': 90,
        'yearly': 365
    }[subscription_type]
    
    amount = {
        'monthly': 29.99,
        'quarterly': 79.99,
        'yearly': 299.99
    }[subscription_type]
    
    start_date = timezone.now()
    end_date = start_date + timedelta(days=duration_days)
    
    subscription = Subscription.objects.create(
        user=request.user,
        subscription_type=subscription_type,
        start_date=start_date,
        end_date=end_date,
        amount=amount,
        payment_id=payment_id
    )
    
    request.user.is_vip = True
    request.user.vip_expire_time = end_date
    request.user.save()
    
    return JsonResponse({
        'subscription': {
            'id': subscription.id,
            'type': subscription.get_subscription_type_display(),
            'start_date': subscription.start_date.isoformat(),
            'end_date': subscription.end_date.isoformat(),
            'amount': float(subscription.amount)
        }
    })

@token_required
@require_http_methods(['GET'])
def subscription_status(request):
    active_subscription = Subscription.objects.filter(
        user=request.user,
        end_date__gt=timezone.now(),
        is_active=True
    ).first()
    
    return JsonResponse({
        'is_vip': request.user.is_vip,
        'vip_expire_time': request.user.vip_expire_time.isoformat() if request.user.vip_expire_time else None,
        'active_subscription': {
            'type': active_subscription.get_subscription_type_display(),
            'end_date': active_subscription.end_date.isoformat(),
        } if active_subscription else None
    })