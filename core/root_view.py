from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

__all__ = ["RootView"]


class RootView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["root"],
    )
    def get(self, request):
        return Response(
            {"message": "Hello, World!"},
            status=status.HTTP_200_OK,
        )
