from django.urls import path

from apps.common.views import StripeWebhookView

urlpatterns = [
    path('webhooks/stripe', StripeWebhookView.as_view(), name='webhooks-stripe')
]

