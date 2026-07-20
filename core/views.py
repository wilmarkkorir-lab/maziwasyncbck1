from django.contrib.auth import get_user_model
from .models import FarmerProfile, PorterProfile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser,IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError, transaction
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()  # returns core.User as defined in AUTH_USER_MODEL

@api_view(['POST'])
@permission_classes([IsAdminUser])  # overrides global IsAuthenticated - anyone can register
@transaction.atomic  # if anything fails, all db changes are rolled back
def Register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    role = request.data.get('role', 'farmer')  # defaults to farmer if not provided
    phone_number = request.data.get('phone_number')

    # validate required fields
    if not username or not password or not email or not phone_number:
        return Response({"error": "Username, password, email and phone number are required"}, status=400)

    # check for duplicates
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already taken"}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    try:
        # create the user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role=role,
            phone_number=phone_number
        )

        # create the matching profile based on role
        if role == 'farmer':
            FarmerProfile.objects.create(
                user=user,
                phone_number=user.phone_number,
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                national_id=request.data.get('national_id'),
            )
        elif role == 'porter':
            PorterProfile.objects.create(
                user=user,
                phone_number=user.phone_number,
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                national_id=request.data.get('national_id'),
                employee_id=request.data.get('employee_id'),
            )

        # single response for all roles
        return Response({
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "message": f"{role.capitalize()} registered successfully"
        }, status=201)

    except IntegrityError as e:
        return Response({"error": "Integrity error: " + str(e)}, status=400)
    except Exception as e:
        return Response({"error": "An error occurred: " + str(e)}, status=500)


# login
@api_view(['POST'])
@permission_classes([AllowAny])
def Login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    print(username, password)
    user = authenticate(request, username=username, password=password)
    if not user:        
        return Response({"error": "Invalid credentials"}, status=401)
    
    Refresh = RefreshToken.for_user(user)
    return Response({
        "username": user.username,
        "role": user.role,
        "access_token": str(Refresh.access_token),
        "refresh_token": str(Refresh),
    })
# get user/profile of the logged in user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def MyProfile(request):
    user = request.user

    profile_data = {}
    # farmer profile
    if getattr(user, 'role', None) == 'farmer' and hasattr(user, 'farmer_profile'):
        p = user.farmer_profile
        profile_data = {
            'first_name': p.first_name,
            'last_name': p.last_name,
            'phone_number': p.phone_number,
            'national_id': p.national_id,
        }
    elif getattr(user, 'role', None) == 'porter' and hasattr(user, 'porter_profile'):
        p = user.porter_profile
        profile_data = {
            'first_name': p.first_name,
            'last_name': p.last_name,
            'employee_id': p.employee_id,
            'route_name': p.route_name,
        }

    return Response({
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'profile': profile_data
    })
# ===========================
    # LOGOUT
# ===========================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Logout(request):
    try:
        refresh_token = request.data.get("refresh_token")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"})
    except TokenError:
        return Response({"error": "Invalid or expired token"}, status=400)
    except Exception as e:
        return Response({"error": str(e)})
      


    