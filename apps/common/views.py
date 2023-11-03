from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import status

from apps.logs.models import Log
from apps.orders.models import Order, Invoice, Cart

from apps.common.helpers import stripe
from config.settings import env

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
            order_id = event['data']['object']['metadata'].get('order_id')
            user_id = event['data']['object']['metadata'].get('user_id')
            payment_intent = event['data']['object'].get('id')

            Order.objects.filter(id=order_id).update(status=order_status)

            if order_status == Order.Status.CONFIRMED:
                Cart.objects.filter(user_id=user_id, is_archived=False).update(is_archived=True)

                Invoice.objects.create(
                    order_id=order_id, status=invoice_status_mapping.get(order_status),
                    stripe_id=payment_intent, user_id=user_id, amount=event['data']['object']['amount']
                )

        return Response(status=status.HTTP_200_OK)


def get_event_from_request(request):
    payload = request.body
    sig_header = request.headers.get('STRIPE_SIGNATURE')
    endpoint_secret = env('STRIPE_ENDPOINT_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError ) as e: # noqa
        raise e

    Log.objects.create(type=event['type'], details=event)
    return event

