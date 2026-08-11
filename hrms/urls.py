"""
URL configuration for hrms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from accounts import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='auth/login.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', views.browser_logout, name='browser_logout'),
    path('forgot-password/', TemplateView.as_view(template_name='auth/forgot-password.html'), name='forgot-password'),
    path('dashboard/', TemplateView.as_view(template_name='HR_admin/index.html'), name='dashboard'),
    path('hr/employee-add/', TemplateView.as_view(template_name='HR_admin/employee-add.html'), name='employee-add'),
    path('hr/employee-service-search/', TemplateView.as_view(template_name='HR_admin/employee-service-search.html'), name='employee-service-search'),
    path('hr/employee-service-record/', TemplateView.as_view(template_name='HR_admin/employee-service-record.html'), name='employee-service-record'),
    path('hr/employee-promotion-history/', TemplateView.as_view(template_name='HR_admin/employee-promotion-history.html'), name='employee-promotion-history'),
    path('hr/employee-promotion-add/', TemplateView.as_view(template_name='HR_admin/employee-promotion-add.html'), name='employee-promotion-add'),
    path('hr/employee-increment-history/', TemplateView.as_view(template_name='HR_admin/employee-increment-history.html'), name='employee-increment-history'),
    path('hr/employee-increment-add/', TemplateView.as_view(template_name='HR_admin/employee-increment-add.html'), name='employee-increment-add'),
    path('hr/employee-transfer-history/', TemplateView.as_view(template_name='HR_admin/employee-transfer-history.html'), name='employee-transfer-history'),
    path('hr/employee-transfer-add/', TemplateView.as_view(template_name='HR_admin/employee-transfer-add.html'), name='employee-transfer-add'),
    path('hr/employee-service/', TemplateView.as_view(template_name='HR_admin/employee-service.html'), name='employee-service'),
    path('hr/employee-promotion-report/', TemplateView.as_view(template_name='HR_admin/employee-promotion-report.html'), name='employee-promotion-report'),
    path('hr/employee-increment-report/', TemplateView.as_view(template_name='HR_admin/employee-increment-report.html'), name='employee-increment-report'),
    path('hr/employee-transfer-report/', TemplateView.as_view(template_name='HR_admin/employee-transfer-report.html'), name='employee-transfer-report'),
    path('hr/employee-profile/', TemplateView.as_view(template_name='HR_admin/employee-profile.html'), name='employee-profile'),
    path('hr/employee-list/', TemplateView.as_view(template_name='HR_admin/employee-list.html'), name='employee-list'),
    path('hr/employee-id-card/', TemplateView.as_view(template_name='HR_admin/employee-id-card.html'), name='employee-id-card'),
    path('hr/employee-resign-list/', TemplateView.as_view(template_name='HR_admin/employee-resign-list.html'), name='employee-resign-list'),
    path('hr/employee-payslip/', TemplateView.as_view(template_name='HR_admin/employee-payslip.html'), name='employee-payslip'),
    path('hr/salary-grade-list/', TemplateView.as_view(template_name='HR_admin/employee-salary-grade-list.html'), name='salary-grade-list'),
    path('hr/salary-grade-add/', TemplateView.as_view(template_name='HR_admin/employee-salary-grade-add.html'), name='salary-grade-add'),
    path('hr/employee-tds/', TemplateView.as_view(template_name='HR_admin/employee-tds.html'), name='employee-tds'),
    path('hr/employee-tds-history/', TemplateView.as_view(template_name='HR_admin/employee-tds-history.html'), name='employee-tds-history'),
    path('hr/employee-tds-add/', TemplateView.as_view(template_name='HR_admin/employee-tds-add.html'), name='employee-tds-add'),
    path('hr/employee-apply-leave/', TemplateView.as_view(template_name='HR_admin/employee-apply-leave.html'), name='employee-apply-leave'),
    path('hr/employee-leave-approved/', TemplateView.as_view(template_name='HR_admin/employee-leave-approved.html'), name='employee-leave-approved'),
    path('hr/make-attendance/', TemplateView.as_view(template_name='HR_admin/make-attendance-view.html'), name='make-attendance'),
    path('hr/attendance-report/', TemplateView.as_view(template_name='HR_admin/employee-attendance-report.html'), name='attendance-report'),
    path('hr/employees-salary-report/', TemplateView.as_view(template_name='HR_admin/employees-salary-report.html'), name='employees-salary-report'),
    path('hr/employees-salary-bank-report/', TemplateView.as_view(template_name='HR_admin/employees-salary-bank-report.html'), name='employees-salary-bank-report'),
    path('hr/employees-esic-report/', TemplateView.as_view(template_name='HR_admin/employees-esic-report.html'), name='employees-esic-report'),
    path('hr/holiday-list/', TemplateView.as_view(template_name='HR_admin/holiday-list.html'), name='holiday-list'),
    path('hr/employee-exit-initiate/', TemplateView.as_view(template_name='HR_admin/employee-exit-initiate.html'), name='employee-exit-initiate'),
    path('inventory/dashboard/', TemplateView.as_view(template_name='inventory_system/index.html'), name='inventory-dashboard'),
    path('inventory/offices/', TemplateView.as_view(template_name='inventory_system/office-list.html'), name='inventory-offices'),
    path('inventory/offices/add/', TemplateView.as_view(template_name='inventory_system/office-add.html'), name='inventory-office-add'),
    path('inventory/categories/', TemplateView.as_view(template_name='inventory_system/category-list.html'), name='inventory-categories'),
    path('inventory/categories/add/', TemplateView.as_view(template_name='inventory_system/category-add.html'), name='inventory-category-add'),
    path('inventory/items/', TemplateView.as_view(template_name='inventory_system/item-list.html'), name='inventory-items'),
    path('inventory/items/add/', TemplateView.as_view(template_name='inventory_system/item-add.html'), name='inventory-item-add'),
    path('inventory/purchases/', TemplateView.as_view(template_name='inventory_system/purchase-list.html'), name='inventory-purchases'),
    path('inventory/purchases/add/', TemplateView.as_view(template_name='inventory_system/purchase-add.html'), name='inventory-purchase-add'),
    path('inventory/issues/employees/', TemplateView.as_view(template_name='inventory_system/item-issue-employees-list.html'), name='inventory-issue-employees'),
    path('inventory/issues/employees/add/', TemplateView.as_view(template_name='inventory_system/item-issue-employees-add.html'), name='inventory-issue-employees-add'),
    path('inventory/issues/department/', TemplateView.as_view(template_name='inventory_system/item-issue-department-list.html'), name='inventory-issue-dept'),
    path('inventory/issues/department/add/', TemplateView.as_view(template_name='inventory_system/item-issue-department-add.html'), name='inventory-issue-dept-add'),
    path('inventory/adjustments/', TemplateView.as_view(template_name='inventory_system/item-adjustment-list.html'), name='inventory-adjustments'),
    path('inventory/adjustments/add/', TemplateView.as_view(template_name='inventory_system/item-adjustment-add.html'), name='inventory-adjustment-add'),
    path('inventory/transfers/', TemplateView.as_view(template_name='inventory_system/item-transfer-list.html'), name='inventory-transfers'),
    path('inventory/transfers/add/', TemplateView.as_view(template_name='inventory_system/item-transfer-add.html'), name='inventory-transfer-add'),
    path('inventory/returned/', TemplateView.as_view(template_name='inventory_system/item-returned-list.html'), name='inventory-returned'),
    path('inventory/returned/add/', TemplateView.as_view(template_name='inventory_system/item-returned-add.html'), name='inventory-returned-add'),
    path('inventory/suppliers/', TemplateView.as_view(template_name='inventory_system/supplier-list.html'), name='inventory-suppliers'),
    path('inventory/suppliers/add/', TemplateView.as_view(template_name='inventory_system/supplier-add.html'), name='inventory-supplier-add'),
    path('user/dashboard/', TemplateView.as_view(template_name='hrms_user/index.html'), name='user-dashboard'),
    path('user/my-profile/', TemplateView.as_view(template_name='hrms_user/my-profile.html'), name='user-my-profile'),
    path('user/my-team/', TemplateView.as_view(template_name='hrms_user/team-list.html'), name='user-my-team'),
    path('user/apply-leave/', TemplateView.as_view(template_name='hrms_user/employee-apply-leave.html'), name='user-apply-leave'),
    path('user/leave-list/', TemplateView.as_view(template_name='hrms_user/employee-leave-list.html'), name='user-leave-list'),
    path('user/team-leaves/', TemplateView.as_view(template_name='hrms_user/team-leaves.html'), name='user-team-leaves'),
    path('user/attendance/', TemplateView.as_view(template_name='hrms_user/employee-attendance-report.html'), name='user-attendance'),
    path('user/payslip/', TemplateView.as_view(template_name='hrms_user/employee-payslip.html'), name='user-payslip'),
    path('user/holidays/', TemplateView.as_view(template_name='hrms_user/holiday-list.html'), name='user-holidays'),
    path('hr/employee-profile/<int:pk>/', TemplateView.as_view(template_name='HR_admin/employee-profile-view.html'), name='employee-profile'),
    path('api/accounts/', include('accounts.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/leave/', include('leave_management.urls')),
    path('api/payroll/', include('payroll.urls')),
    path('api/assets/', include('asset_management.urls')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
