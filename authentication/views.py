from django.shortcuts import render
from rest_framework import generics, permissions, status
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, MyTokenObtainPairSerializer, UserSerializer, CustomerListSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

# Create your views here.

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    @transaction.atomic  # This ensures both user and profile are created or neither
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "message": "User created successfully"
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "message": "User creation failed",
                "errors": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

# Test endpoint to show user role information
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_role(request):
    """
    Test endpoint to show user role information
    """
    user = request.user
    role = "business_owner" if user.groups.filter(name='Business Owners').exists() else "user"
    
    return Response({
        "username": user.username,
        "email": user.email,
        "full_name": f"{user.first_name} {user.last_name}".strip(),
        "role": role,
        "groups": [group.name for group in user.groups.all()]
    })

class CustomerListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CustomerListSerializer

    def get_queryset(self):
        # Get all users who are not in the Business Owners group
        return User.objects.exclude(groups__name='Business Owners').order_by('first_name', 'last_name')
