from django.urls import path

from apps.common.views import StripeWebhookView

app_name = 'apps.common'

urlpatterns = [
    path('webhooks/stripe', StripeWebhookView.as_view(), name='webhook-stripe')
]

