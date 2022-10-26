from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CategoriesViewSet, CommentViewSet, GenresViewSet,
                    ReviewViewSet, TitlesViewSet, SingupView,
                    TokenView, UserViewSet)

router = DefaultRouter()
router.register(r'categories', CategoriesViewSet)
router.register(r'genres', GenresViewSet)
router.register(r'titles', TitlesViewSet)
router.register(r'titles/(?P<title_id>\d+)/reviews',
                ReviewViewSet, basename='reviews')
router.register(r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)'
                r'/comments', CommentViewSet, basename='comments')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [

    path('v1/auth/signup/', SingupView.as_view(), name='register'),
    path('v1/auth/token/', TokenView.as_view(), name='token'),
    path('v1/', include(router.urls)),
]
