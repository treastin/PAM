from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView


from apps.users.views import UserSignupViewSet, UserLoginViewSet, UserProfileViewSet, UserAddressViewSet

router = DefaultRouter()
router.register('signup', UserSignupViewSet, 'signup')
router.register('login', UserLoginViewSet, 'login')
router.register('user-profile', UserProfileViewSet, 'user-profile')
router.register('user-address', UserAddressViewSet, 'user-address')

urlpatterns = router.urls

urlpatterns += [
    path("user/login", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("user/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("user/logout",TokenBlacklistView.as_view(), name="token_blacklist")
]
