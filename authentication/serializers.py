from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'], required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'full_name', 'phone_number', 'gender')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Split full name into first_name and last_name
        full_name_parts = validated_data['full_name'].split(' ', 1)
        first_name = full_name_parts[0]
        last_name = full_name_parts[1] if len(full_name_parts) > 1 else ''

        # Remove fields that aren't part of the User model
        validated_data.pop('password2')
        validated_data.pop('full_name')
        phone_number = validated_data.pop('phone_number')
        gender = validated_data.pop('gender', None)

        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=first_name,
            last_name=last_name
        )
        
        user.set_password(validated_data['password'])
        user.save()

        # Create or update user profile
        UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            gender=gender
        )

        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Add extra responses here
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['full_name'] = f"{self.user.first_name} {self.user.last_name}".strip()
        if hasattr(self.user, 'profile'):
            data['phone_number'] = self.user.profile.phone_number
            data['gender'] = self.user.profile.gender
        return data

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='profile.phone_number')
    gender = serializers.CharField(source='profile.gender', required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'full_name', 'phone_number', 'gender')
        read_only_fields = ('id',)

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()