from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from apps.common.permisions import IsAdmin
from apps.logs.models import Log
from apps.logs.serializers import LogSerializer

# Create your views here.


class LogViewSet(GenericViewSet, ListModelMixin):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = (IsAuthenticated, IsAdmin,)
    filterset_fields = ('event_type',)
