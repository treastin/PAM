from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, mixins, GenericViewSet

from apps.products.serializers import ProductSerializer, ProductCategorySerializer, ProductReviewSerializer, \
    ProductAttachmentsSerializer
from apps.products.models import Products, ProductReview, ProductCategory, ProductAttachments
from apps.common.permisions import IsAdmin, IsAdminOrOwner, ReadOnly

# Create your views here.


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Products.objects.all()
    permission_classes = (IsAuthenticated, IsAdmin | ReadOnly)
    filterset_fields = ('category',)

    @action(detail=False, methods=['GET'])
    def best_sellers(self, request, *args, **kwargs):
        queryset = (self.filter_queryset(self.get_queryset())
                    .exclude(carts__price=None).annotate(sold=Count('carts')).order_by('sold'))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return self.get_serializer(queryset, many=True)


class ProductCategoryViewSet(ModelViewSet):
    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()
    permission_classes = (IsAuthenticated, IsAdmin | ReadOnly)
    parser_classes = (MultiPartParser,)


class ProductReviewViewSet(ModelViewSet):
    serializer_class = ProductReviewSerializer
    queryset = ProductReview.objects.all()
    permission_classes = (IsAuthenticated, IsAdminOrOwner | ReadOnly)
    filterset_fields = ('product', 'rating',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductAttachmentsViewSet(ModelViewSet):
    serializer_class = ProductAttachmentsSerializer
    queryset = ProductAttachments.objects.all()
    permission_classes = (IsAuthenticated, IsAdmin | ReadOnly)
    parser_classes = (MultiPartParser,)
    filterset_fields = ('product',)
