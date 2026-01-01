from django.contrib import admin
from .models import OTPVerification, QuestionPaper, StudentNotification, Internship

admin.site.register(OTPVerification)
admin.site.register(QuestionPaper)
admin.site.register(StudentNotification)
admin.site.register(Internship)