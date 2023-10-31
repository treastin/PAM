from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import status

from apps.orders.models import Order

from apps.common.helpers import stripe
from config.settings import env

status_mapping = {
    'payment_intent.succeeded': Order.Status.CONFIRMED,

    'payment_intent.canceled': Order.Status.CANCELED,
    'payment_intent.payment_failed': Order.Status.CANCELED,
}


class StripeWebhookView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):

        event = get_event_from_request(request)
        order_status = status_mapping.get(event['type'])

        if order_status:
            order_id = event['data']['object']['metadata'].get('order_id')
            Order.objects.filter(id=order_id).update(status=order_status)

        return Response(status=status.HTTP_200_OK)


def get_event_from_request(request):
    payload = request.body
    sig_header = request.headers['STRIPE_SIGNATURE']
    endpoint_secret = env('STRIPE_ENDPOINT_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        raise e

    except stripe.error.SignatureVerificationError as e:  # noqa
        raise e

    return event

