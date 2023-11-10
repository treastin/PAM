from json import loads
from drf_util.utils import gt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import status

from apps.logs.models import Log
from apps.orders.models import Order, Invoice, Cart

from apps.common.helpers import stripe
from config import settings

status_mapping = {
    'payment_intent.succeeded': Order.Status.CONFIRMED,
    'payment_intent.canceled': Order.Status.CANCELED,
    'payment_intent.payment_failed': Order.Status.CANCELED,
}
invoice_status_mapping = {
    Order.Status.CONFIRMED: 'completed',
    Order.Status.CANCELED: 'canceled'
}


class StripeWebhookView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):

        event = get_event_from_request(request)

        order_status = status_mapping.get(event['type'])

        if order_status:
            order_id = gt(event, 'data.object.metadata.order_id')
            user_id = gt(event, 'data.object.metadata.user_id')

            Order.objects.filter(id=order_id).update(status=order_status)

            if order_status == Order.Status.CONFIRMED:
                Cart.objects.filter(user_id=user_id, is_archived=False).update(is_archived=True)

                Invoice.objects.filter(order_id=order_id).update(status=Invoice.Status.SUCCEEDED)

            elif order_status == Order.Status.CANCELED:
                Invoice.objects.filter(order_id=order_id).update(status=Invoice.Status.CANCELED)

        return Response(status=status.HTTP_200_OK)


def get_event_from_request(request):
    payload = request.body
    sig_header = request.headers.get('STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    event = {}
    error_message = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        error_message = e

    if event:
        event_type = event.get('type')
        details = event.copy()
    else:
        event_type = 'Error'
        details = {'request_body': loads(request.body)}

    Log.objects.create(event_type=event_type, details=details, error_message=error_message)
    return event

