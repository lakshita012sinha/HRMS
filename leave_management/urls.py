from django.urls import path
from .views import (
    LeaveTypeListCreateView, LeaveTypeDetailView,
    LeaveBalanceListView, LeaveBalanceCreateView, MyLeaveBalanceView,
    LeaveRequestListView, LeaveRequestDetailView,
    ApplyLeaveView, ApproveLeaveView, CancelLeaveView,
    LeavePolicyListCreateView, LeavePolicyDetailView
)

urlpatterns = [
    # Leave Types
    path('leave-types/', LeaveTypeListCreateView.as_view(), name='leave-type-list-create'),
    path('leave-types/<int:pk>/', LeaveTypeDetailView.as_view(), name='leave-type-detail'),
    
    # Leave Balance
    path('leave-balances/', LeaveBalanceListView.as_view(), name='leave-balance-list'),
    path('leave-balances/create/', LeaveBalanceCreateView.as_view(), name='leave-balance-create'),
    path('my-leave-balance/', MyLeaveBalanceView.as_view(), name='my-leave-balance'),
    
    # Leave Requests
    path('leave-requests/', LeaveRequestListView.as_view(), name='leave-request-list'),
    path('leave-requests/<int:pk>/', LeaveRequestDetailView.as_view(), name='leave-request-detail'),
    path('apply-leave/', ApplyLeaveView.as_view(), name='apply-leave'),
    path('leave-requests/<int:pk>/approve/', ApproveLeaveView.as_view(), name='approve-leave'),
    path('leave-requests/<int:pk>/cancel/', CancelLeaveView.as_view(), name='cancel-leave'),
    
    # Leave Policies
    path('leave-policies/', LeavePolicyListCreateView.as_view(), name='leave-policy-list-create'),
    path('leave-policies/<int:pk>/', LeavePolicyDetailView.as_view(), name='leave-policy-detail'),
]
