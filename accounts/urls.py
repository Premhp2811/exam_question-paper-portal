from django.urls import path
from . import views

urlpatterns = [
    path('', views.role_selection_view, name='role_selection'),
    path('student-login/', views.login_view, name='student_login'),
    path('college-selection/', views.college_selection_view, name='college_selection'),
    path('teacher-login/<str:college>/', views.teacher_login_view, name='teacher_login_college'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('student-college-selection/', views.student_college_selection_view, name='student_college_selection'),
    path('student-select-college/<str:college>/', views.student_select_college_view, name='student_select_college'),
    path('branch-selection/', views.branch_selection_view, name='branch_selection'),
    path('semester-selection/<str:branch>/', views.semester_selection_view, name='semester_selection'),
    path('teacher-dashboard/<str:branch>/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('upload-notes/<str:branch>/<str:semester>/', views.upload_notes_view, name='upload_notes'),
    path('select-semester-upload/<str:branch>/', views.select_semester_upload_view, name='select_semester_upload'),
    path('upload-type-selection/<str:branch>/<str:semester>/', views.upload_type_selection_view, name='upload_type_selection'),
    path('upload-document/<str:branch>/<str:semester>/<str:doc_type>/', views.upload_document_view, name='upload_document'),
    path('manage-papers/<str:branch>/', views.manage_papers_view, name='manage_papers'),
    path('delete-paper/<int:paper_id>/', views.delete_paper_view, name='delete_paper'),
    path('view-notes/<str:branch>/<str:semester>/', views.view_notes_view, name='view_notes'),
    path('internships/<str:branch>/', views.internships_view, name='internships'),
    path('student-upload-verify/<str:branch>/<str:semester>/', views.student_upload_verify_view, name='student_upload_verify'),
    path('student-upload-form/<str:branch>/<str:semester>/', views.student_upload_form_view, name='student_upload_form'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
]