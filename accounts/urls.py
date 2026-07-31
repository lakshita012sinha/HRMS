from django.urls import path
from .views import (
    UserRegistrationView, LoginView, LogoutView,
    ChangePasswordView, PasswordResetRequestView, PasswordResetConfirmView,
    UserProfileView, UserListView, UserDetailView,
    RoleListCreateView, RoleDetailView,
    PermissionListCreateView, PermissionDetailView,
    BranchListCreateView, BranchDetailView,
    DepartmentListCreateView, DepartmentDetailView,
    DesignationListCreateView, DesignationDetailView,
    EmployeeDetailAPIView, EmployeeListAPIView, PastEmployeeListView, PastEmployeeDetailView,
    EmployeeDocumentUploadView, EmployeePhotoUploadView, EmployeeSoftDeleteView,
    PromotionListCreateView, IncrementListCreateView, TransferListCreateView
)

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password management
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # User management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('employees/', EmployeeListAPIView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', EmployeeDetailAPIView.as_view(), name='employee-detail'),
    path('employees/<int:pk>/documents/', EmployeeDocumentUploadView.as_view(), name='employee-documents'),
    path('employees/<int:pk>/photo/', EmployeePhotoUploadView.as_view(), name='employee-photo'),
    path('employees/<int:pk>/exit/', EmployeeSoftDeleteView.as_view(), name='employee-exit'),
    
    # Past employees
    path('past-employees/', PastEmployeeListView.as_view(), name='past-employee-list'),
    path('past-employees/<int:pk>/', PastEmployeeDetailView.as_view(), name='past-employee-detail'),
    
    # Role management
    path('roles/', RoleListCreateView.as_view(), name='role-list'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role-detail'),
    
    # Permission management
    path('permissions/', PermissionListCreateView.as_view(), name='permission-list'),
    path('permissions/<int:pk>/', PermissionDetailView.as_view(), name='permission-detail'),
    
    # Organization structure
    path('branches/', BranchListCreateView.as_view(), name='branch-list'),
    path('branches/<int:pk>/', BranchDetailView.as_view(), name='branch-detail'),
    path('departments/', DepartmentListCreateView.as_view(), name='department-list'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),
    path('designations/', DesignationListCreateView.as_view(), name='designation-list'),
    path('designations/<int:pk>/', DesignationDetailView.as_view(), name='designation-detail'),
    path('promotions/', PromotionListCreateView.as_view(), name='promotion-list'),
    path('increments/', IncrementListCreateView.as_view(), name='increment-list'),
    path('transfers/', TransferListCreateView.as_view(), name='transfer-list'),
]
