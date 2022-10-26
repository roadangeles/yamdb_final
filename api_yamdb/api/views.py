import logging
from uuid import uuid4

from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Categories, Genres, Review, Title
from users.models import User

from api_yamdb.settings import DOMAIN_NAME

from .filters import TitlesFilter
from .mixins import ListCreateDestroyViewSet
from .permissions import Admin, AdminOrModeratorOrOwnerOrReadOnly, UserAdmin
from .serializers import (CategoriesSerializer, CommentSerializer,
                          GenresSerializer, ReviewSerializer, SignupSerializer,
                          TitlesCreateSerializer, TitlesSerializer,
                          TokenSerializer, UserSerializer,
                          )

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w')
logger = logging.getLogger(__name__)


class CategoriesViewSet(ListCreateDestroyViewSet):
    """API для работы с моделью категорий."""
    queryset = Categories.objects.all()
    serializer_class = CategoriesSerializer
    permission_classes = (Admin,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenresViewSet(ListCreateDestroyViewSet):
    """API для работы с моделью жанров."""
    queryset = Genres.objects.all()
    serializer_class = GenresSerializer
    permission_classes = (Admin,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitlesViewSet(viewsets.ModelViewSet):
    """API для работы с моделью произведений."""
    queryset = Title.objects.all().annotate(
        Avg("reviews__score")
    ).order_by("name")
    serializer_class = TitlesSerializer
    permission_classes = (Admin,)
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter
    ordering_fields = ('name',)
    ordering = ('name',)

    def get_serializer_class(self):
        if self.action in ("retrieve", "list"):
            return TitlesCreateSerializer
        return TitlesSerializer


class SingupView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        confirmation_code = uuid4()
        send_mail(
            subject="YaMDb registration",
            message=f"Your confirmation code: {confirmation_code}",
            from_email=f"singup@{DOMAIN_NAME}",
            recipient_list=[serializer.validated_data['email']],
        )
        serializer.save(confirmation_code=confirmation_code)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User,
            username=serializer.validated_data["username"]
        )
        if (serializer.validated_data['confirmation_code']
                == user.confirmation_code):
            refresh = RefreshToken.for_user(user)

            return Response(str(refresh.access_token),
                            status=status.HTTP_200_OK)
        return Response('Не верный код',
                        status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    pagination_class = PageNumberPagination
    permission_classes = (UserAdmin,)
    lookup_field = 'username'

    @action(
        detail=False,
        methods=["get", "patch"],
        name="Set info about yourself",
        url_path=r'me',
        url_name="me",
        permission_classes=[permissions.IsAuthenticated, ]
    )
    def getpatch(self, request):

        serializer = UserSerializer(
            request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if request.method == 'PATCH':
            serializer.save(role=request.user.role, partial=True)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [AdminOrModeratorOrOwnerOrReadOnly]

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get("title_id"))

        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [AdminOrModeratorOrOwnerOrReadOnly]

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(
            Review.objects.filter(title_id=title_id), id=review_id
        )
        return review.comments.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(
            Review.objects.filter(title_id=title_id), id=review_id
        )
        serializer.save(author=self.request.user, review=review)
