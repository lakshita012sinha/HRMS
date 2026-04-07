from django.urls import path
from .views import (
    SalaryStructureListCreateView, SalaryStructureDetailView, MySalaryStructureView,
    SalaryListView, SalaryDetailView,
    GenerateSalaryView, MarkSalaryPaidView, CancelSalaryView, MySalaryView,
    CreateCTCSalaryStructureView, GenerateMonthlyPayrollView
)

urlpatterns = [
    # Salary Structure
    path('salary-structures/', SalaryStructureListCreateView.as_view(), name='salary-structure-list-create'),
    path('salary-structures/<int:pk>/', SalaryStructureDetailView.as_view(), name='salary-structure-detail'),
    path('create-ctc-structure/', CreateCTCSalaryStructureView.as_view(), name='create-ctc-structure'),
    path('my-salary-structure/', MySalaryStructureView.as_view(), name='my-salary-structure'),
    
    # Salary
    path('salaries/', SalaryListView.as_view(), name='salary-list'),
    path('salaries/<int:pk>/', SalaryDetailView.as_view(), name='salary-detail'),
    path('generate-salary/', GenerateSalaryView.as_view(), name='generate-salary'),
    path('salaries/<int:pk>/mark-paid/', MarkSalaryPaidView.as_view(), name='mark-salary-paid'),
    path('salaries/<int:pk>/cancel/', CancelSalaryView.as_view(), name='cancel-salary'),
    path('my-salaries/', MySalaryView.as_view(), name='my-salaries'),
    path('generate-monthly-payroll/', GenerateMonthlyPayrollView.as_view(), name='generate-monthly-payroll'),
]
