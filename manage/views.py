from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Branch, Bank
from .serializers import BranchCreateSerializer, BranchSerializer
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import viewsets
from SimpleBank.utils.bonusRenderer import BonusResponseRenderer


class BranchViewSet(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = BranchCreateSerializer
    response_serializer_class = BranchSerializer
    renderer_classes = [BonusResponseRenderer, ]

    def list(self, request):
        queryset = Branch.objects.filter(bank__id=request.user.bank.id)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = Branch.objects.filter(bank__id=request.user.bank.id)
        branch = get_object_or_404(queryset, pk=pk)
        serializer = self.response_serializer_class(branch)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(self.response_serializer_class(Branch.objects.get(pk=serializer.data.get('id'))).data,
                            status=status.HTTP_201_CREATED)
        else:
            response = {'detail': serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
