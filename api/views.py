from datetime import datetime

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import TitleFilter
from .models import Category, Genre, Review, Title, User
from .permissions import CustomPermission, IsAdminUserOrReadOnly, IsSuperUser
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer,
                          TitleReadSerializer, TitleWriteSerializer,
                          UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = (IsSuperUser,)
    lookup_field = "username"

    @action(
        methods=["get", "patch"],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, pk=None):
        if request.method == "GET":
            serializer = UserSerializer(self.request.user)
            return Response(serializer.data)
        if request.method == "PATCH":
            user = get_object_or_404(User, username=self.request.user)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.data, status=status.HTTP_400_BAD_REQUEST
            )


@api_view(["POST"])
@permission_classes([AllowAny])
def send_confirmation_code(request):
    email = request.data["email"]
    username = email.split("@")[0]
    user = User.objects.create(
        username=username,
        email=email,
        last_login=datetime.now(),
    )
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        "Confirmation code",
        f"{confirmation_code}",
        f"{settings.ADMIN_EMAIL}",  # Это поле "От кого"
        [f"{email}"],  # Это поле "Кому" (можно указать список адресов)
        fail_silently=False,  # Сообщать об ошибках («молчать ли об ошибках?»)
    )
    return Response(confirmation_code, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def send_token(request):
    email = request.data["email"]
    user = get_object_or_404(User, username=email.split("@")[0])
    confirmation_code = request.data["confirmation_code"]
    refresh = RefreshToken.for_user(user)
    response = {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }
    if default_token_generator.check_token(user, confirmation_code):
        user.is_active = True
        user.save()
        return JsonResponse(response)
    else:
        message = "Ops! Bad wrong!"
        return JsonResponse(
            {"status": "false", "message": message}, status=500
        )


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(rating=Avg("reviews__score"))
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method in ["POST", "PATCH"]:
            return TitleWriteSerializer
        return TitleReadSerializer


class MixinSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    pass


class CategoryViewSet(MixinSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = [filters.SearchFilter]
    search_fields = ["=name"]
    lookup_field = "slug"


class GenreViewSet(MixinSet):
    queryset = Genre.objects.all().order_by("id")
    serializer_class = GenreSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = [filters.SearchFilter]
    search_fields = ["=name"]
    lookup_field = "slug"


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (CustomPermission,)

    def get_serializer_context(self):
        context = super(ReviewViewSet, self).get_serializer_context()
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        context.update({'title': title})
        return context

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        return title.reviews.all().order_by('id')

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (CustomPermission,)

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            title_id=self.kwargs.get('title_id'),
            id=self.kwargs.get('review_id')
        )
        return review.comments.all().order_by('id')

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            title_id=self.kwargs.get('title_id'),
            id=self.kwargs.get('review_id')
        )
        user = get_object_or_404(User, username=self.request.user)
        serializer.save(author=user, review=review)
