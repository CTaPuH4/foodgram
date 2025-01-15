from rest_framework import serializers


class IsSubscribedMixin(serializers.Serializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj in user.subs.all()
