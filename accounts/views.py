from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.db import transaction
from .models import User, Role, Permission
from .models_extended import Branch, Department, Designation
from .models_past_employees import PastEmployee
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ChangePasswordSerializer, RoleSerializer, PermissionSerializer
)
from .serializers_employee import CompleteEmployeeRegistrationSerializer, EmployeeDetailSerializer
from .serializers_extended import BranchSerializer, DepartmentSerializer, DesignationSerializer
from .serializers_update import EmployeeUpdateSerializer
from .serializers_past_employees import PastEmployeeSerializer, DeleteEmployeeSerializer


class UserRegistrationView(generics.CreateAPIView):
    """API endpoint for complete employee registration by HR/Admin"""
    queryset = User.objects.all()
    serializer_class = CompleteEmployeeRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            raise PermissionDenied("Only HR and Admin can register employees")

        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'user': EmployeeDetailSerializer(user).data,
            'message': f'Employee created successfully. User ID: {user.user_id}',
            'user_id': user.user_id,
            'id': user.id,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """API endpoint for user login"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """API endpoint for user logout"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """API endpoint for changing password"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            return Response({'message': 'Password reset link sent', 'uid': uid, 'token': token}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'Password reset link sent'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64, token):
        from .serializers import PasswordResetConfirmSerializer as PRC
        serializer = PRC(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View and update logged-in user profile"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EmployeeUpdateSerializer
        return EmployeeDetailSerializer

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role and user.role.name in ['HR', 'ADMIN']:
            return User.objects.all()
        return User.objects.filter(id=user.id)


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


# ── Role & Permission ─────────────────────────────────────────────────────────

class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]


class PermissionListCreateView(generics.ListCreateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]


class PermissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]


# ── Org Structure ─────────────────────────────────────────────────────────────

class BranchListCreateView(generics.ListCreateAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]


class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class DesignationListCreateView(generics.ListCreateAPIView):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    permission_classes = [permissions.IsAuthenticated]


# ── Employee APIs ─────────────────────────────────────────────────────────────

class EmployeeListAPIView(generics.ListAPIView):
    """List all employees (users with an EmployeeProfile)"""
    serializer_class = EmployeeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models_extended import EmployeeProfile
        from django.db.models import Q
        emp_user_ids = EmployeeProfile.objects.values_list('user_id', flat=True)
        qs = User.objects.filter(id__in=emp_user_ids).order_by('user_id')
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(user_id__icontains=search)
            )
        return qs


class EmployeeDetailAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a single employee"""
    serializer_class = EmployeeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = EmployeeUpdateSerializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(EmployeeDetailSerializer(user).data)


# ── Past Employees ────────────────────────────────────────────────────────────

class PastEmployeeListView(generics.ListAPIView):
    queryset = PastEmployee.objects.all()
    serializer_class = PastEmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]


class PastEmployeeDetailView(generics.RetrieveAPIView):
    queryset = PastEmployee.objects.all()
    serializer_class = PastEmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]


# ── Document Upload ───────────────────────────────────────────────────────────

class EmployeeDocumentUploadView(APIView):
    """Upload documents for an employee."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from .models_extended import EmployeeProfile, EmployeeDocument
        try:
            profile = EmployeeProfile.objects.get(user__id=pk)
        except EmployeeProfile.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        document_type = request.data.get('document_type')
        document_file = request.FILES.get('document_file')

        if not document_type or not document_file:
            return Response({'error': 'document_type and document_file are required'}, status=status.HTTP_400_BAD_REQUEST)

        doc = EmployeeDocument.objects.create(
            employee=profile,
            document_type=document_type,
            document_file=document_file,
        )
        return Response({
            'id': doc.id,
            'document_type': doc.get_document_type_display(),
            'document_file': doc.document_file.url,
            'status': doc.get_status_display(),
        }, status=status.HTTP_201_CREATED)


class EmployeePhotoUploadView(APIView):
    """Upload/update profile photo for an employee."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from .models_extended import EmployeeProfile
        try:
            profile = EmployeeProfile.objects.get(user__id=pk)
        except EmployeeProfile.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        photo = request.FILES.get('profile_photo')
        if not photo:
            return Response({'error': 'profile_photo file is required'}, status=status.HTTP_400_BAD_REQUEST)

        profile.profile_photo = photo
        profile.save()
        return Response({'profile_photo': profile.profile_photo.url}, status=status.HTTP_200_OK)


class EmployeeSoftDeleteView(APIView):
    """Soft-delete an employee — saves to PastEmployee and deactivates the user."""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response({'error': 'Only HR and Admin can initiate employee exit'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        from .models_past_employees import PastEmployee
        from .models_extended import EmployeeProfile, EmploymentDetails, EmergencyContact, BankDetails
        import json

        # Gather profile data
        profile_data, employment_data, emergency_data, bank_data = None, None, None, None
        date_of_joining = None
        try:
            p = EmployeeProfile.objects.get(user=user)
            date_of_joining = p.date_of_joining
            profile_data = {
                'father_name': p.father_name, 'mother_name': p.mother_name,
                'date_of_birth': str(p.date_of_birth) if p.date_of_birth else None,
                'gender': p.gender, 'blood_group': p.blood_group,
                'marital_status': p.marital_status, 'contact_number': p.contact_number,
                'uid_number': p.uid_number, 'pan_number': p.pan_number,
                'qualification': p.qualification,
                'present_address': p.present_address, 'present_city': p.present_city,
                'present_state': p.present_state,
            }
        except Exception:
            pass

        try:
            ed = EmploymentDetails.objects.get(employee__user=user)
            employment_data = {
                'branch': ed.branch.name if ed.branch else None,
                'department': ed.department.name if ed.department else None,
                'designation': ed.designation.name if ed.designation else None,
                'grade': ed.grade, 'employment_type': ed.employment_type,
            }
        except Exception:
            pass

        try:
            ec = EmergencyContact.objects.get(employee__user=user)
            emergency_data = {
                'relationship_name': ec.relationship_name,
                'relationship_type': ec.relationship_type,
                'parent_mobile': ec.parent_mobile,
            }
        except Exception:
            pass

        try:
            from .models_extended import BankDetails
            bd = BankDetails.objects.get(employee__user=user)
            bank_data = {
                'bank_name': bd.bank_name, 'account_number': bd.account_number,
                'ifsc_code': bd.ifsc_code,
            }
        except Exception:
            pass

        deletion_reason = request.data.get('deletion_reason', '')
        last_working_day = request.data.get('last_working_day') or None

        # Create PastEmployee record
        past = PastEmployee.objects.create(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role_name=user.role.name if user.role else '',
            profile_data=profile_data,
            employment_data=employment_data,
            emergency_contact_data=emergency_data,
            bank_data=bank_data,
            deleted_by=request.user,
            deletion_reason=deletion_reason,
            date_joined=user.date_joined,
            date_of_joining=date_of_joining,
            last_working_day=last_working_day,
        )

        # Deactivate user (soft delete)
        user.is_active = False
        user.save()

        return Response({
            'message': f'Employee {user.user_id} exit initiated successfully.',
            'past_employee_id': past.id,
        }, status=status.HTTP_201_CREATED)
