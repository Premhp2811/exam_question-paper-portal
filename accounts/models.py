from django.db import models
from django.utils import timezone
from datetime import timedelta
import random

class OTPVerification(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def is_valid(self):
        # OTP valid for 10 minutes
        return timezone.now() < self.created_at + timedelta(minutes=10)
    
    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} - {self.otp}"


class QuestionPaper(models.Model):
    BRANCH_CHOICES = [
        ('cse', 'Computer Science & Engineering'),
        ('civil', 'Civil Engineering'),
        ('auto', 'Automobile Engineering'),
        ('eee', 'Electrical & Electronics Engineering'),
        ('ece', 'Electronics & Communication Engineering'),
        ('ist', 'Information Science & Technology'),
        ('ice', 'Instrumentation & Control Engineering'),
        ('mech', 'Mechanical Engineering'),
    ]
    
    SEMESTER_CHOICES = [
        ('1', '1st Semester'),
        ('2', '2nd Semester'),
        ('3', '3rd Semester'),
        ('4', '4th Semester'),
        ('5', '5th Semester'),
        ('6', '6th Semester'),
    ]
    
    DOC_TYPE_CHOICES = [
        ('notes', 'Notes'),
        ('syllabus', 'Syllabus'),
        ('midterm', 'Midterm Papers'),
        ('model', 'Model Papers'),
    ]
    
    COLLEGE_CHOICES = [
        ('meip', 'MEIP'),
        ('pvp', 'PVP'),
        ('sjp', 'SJP'),
        ('rrp', 'RRP'),
    ]
    
    branch = models.CharField(max_length=10, choices=BRANCH_CHOICES)
    college = models.CharField(max_length=10, choices=COLLEGE_CHOICES, default='meip')
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='notes')
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    year = models.IntegerField()
    uploaded_by = models.CharField(max_length=100)
    file = models.FileField(upload_to='question_papers/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.branch} - Sem {self.semester}"


class StudentNotification(models.Model):
    email = models.EmailField()
    college = models.CharField(max_length=10)
    branch = models.CharField(max_length=10, blank=True, null=True)
    semester = models.CharField(max_length=2, blank=True, null=True)
    wants_notifications = models.BooleanField(default=True)
    last_viewed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.email} - {self.college} - {self.branch or 'All'} - Sem {self.semester or 'All'}"
class Internship(models.Model):
    BRANCH_CHOICES = [
        ('cse', 'Computer Science & Engineering'),
        ('ist', 'Information Science & Technology'),
        ('both', 'Both CSE & ISE'),
    ]
    
    company_name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    logo_initials = models.CharField(max_length=5, default='CO')
    location = models.CharField(max_length=200)
    duration = models.CharField(max_length=100)
    branch = models.CharField(max_length=10, choices=BRANCH_CHOICES)
    description = models.TextField(blank=True, null=True)
    skills = models.CharField(max_length=500, help_text="Comma-separated skills")
    apply_link = models.URLField()
    is_active = models.BooleanField(default=True)
    posted_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-posted_date']
    
    def __str__(self):
        return f"{self.company_name} - {self.role}"
    
    def get_skills_list(self):
        return [skill.strip() for skill in self.skills.split(',')]