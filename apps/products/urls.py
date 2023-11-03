from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.products.views import ProductReviewViewSet,ProductAttachmentsViewSet, ProductCategoryViewSet, ProductViewSet

router = DefaultRouter()

router.register('product', ProductViewSet, 'product')
router.register('product-attachments', ProductAttachmentsViewSet, 'attachments')
router.register('product-review', ProductReviewViewSet, 'review')
router.register('product-category', ProductCategoryViewSet, 'category')


urlpatterns = router.urls
