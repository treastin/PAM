from rest_framework import serializers


from apps.products.models import Products, ProductCategory, ProductReview, ProductAttachments


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = '__all__'

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'deleted_at'
        ]


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'

        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]


class ProductAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttachments
        fields = [
            'id',
            'created_at',
            'updated_at',
            'attachment',
            'product',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]


class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = '__all__'

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'user',
        ]
