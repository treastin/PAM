from rest_framework.routers import DefaultRouter

from apps.orders.views import OrderViewSet, CartViewSet

router = DefaultRouter()

router.register('order', OrderViewSet,'order')
router.register('cart', CartViewSet, 'cart')

urlpatterns = router.urls

