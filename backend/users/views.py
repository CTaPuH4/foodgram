from django.db.models import Count
from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.paginators import CustomPagination
from users.models import CustomUser
from users.serializers import (AvatarUpdateSerializer,
                               ChangePasswordSerializer,
                               CustomUserRecipesSerializer,
                               CustomUserSerializer)


class CustomUserViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = []

    @action(detail=False,
            methods=('get',),
            permission_classes=[permissions.IsAuthenticated],
            url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False,
            methods=('put', 'delete'),
            permission_classes=[permissions.IsAuthenticated],
            url_path='me/avatar')
    def update_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarUpdateSerializer(
                instance=user,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"avatar": request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=[permissions.IsAuthenticated],
            url_path='subscribe')
    def subs_add(self, request, pk=None):
        user = request.user
        sub = self.get_object()

        if request.method == 'POST':
            if user.pk == sub.pk:
                return Response(
                    {'detail': 'Вы не можете подписаться на себя самого.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif user.subs.filter(pk=sub.pk).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на данного пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.subs.add(sub)
            subscription = CustomUser.objects.annotate(
                recipes_count=Count('recipes')).get(pk=sub.pk)
            serializer = CustomUserRecipesSerializer(
                subscription,
                context={'request': self.request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not user.subs.filter(pk=sub.pk).exists():
                return Response(
                    {'detail': 'Вы не подписаны на данного пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.subs.remove(sub)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('get',),
            permission_classes=[permissions.IsAuthenticated],
            url_path='subscriptions')
    def subs_list(self, request):
        user = request.user
        subscriptions = user.subs.annotate(recipes_count=Count('recipes'))

        paginator = CustomPagination()
        paginated_data = paginator.paginate_queryset(subscriptions, request)

        serializer = CustomUserRecipesSerializer(
            paginated_data,
            many=True,
            context={'request': self.request}
        )
        return paginator.get_paginated_response(serializer.data)


class ChangePasswordViewSet(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
