from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, mixins , GenericViewSet

from apps.products.serializers import ProductSerializer, ProductCategorySerializer, ProductReviewSerializer, \
    ProductAttachmentsSerializer
from apps.products.models import Products, ProductReview, ProductCategory, ProductAttachments
from apps.common.permisions import IsAdmin, IsAdminOrItself, ReadOnly

# Create your views here.


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Products.objects.all()
    permission_classes = (IsAuthenticated, IsAdmin | ReadOnly)
    filterset_fields = ('category',)


class ProductCategoryViewSet(ModelViewSet):
    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()
    permission_classes = (IsAuthenticated, IsAdmin | ReadOnly)
    parser_classes = (MultiPartParser,)


class ProductReviewViewSet(GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                           mixins.CreateModelMixin):
    serializer_class = ProductReviewSerializer
    queryset = ProductReview.objects.all()
    permission_classes = (IsAuthenticated, IsAdminOrItself | ReadOnly)
    filterset_fields = ('product', 'rating',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductAttachmentsViewSet(ModelViewSet):
    serializer_class = ProductAttachmentsSerializer
    queryset = ProductAttachments.objects.all()
    permission_classes = (IsAuthenticated, IsAdmin | ReadOnly)
    parser_classes = (MultiPartParser,)
    filterset_fields = ('product',)

