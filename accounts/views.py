from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .models import OTPVerification, QuestionPaper, StudentNotification, Internship
from django.db import models

def send_upload_notification(college, branch, semester, doc_type, title, subject, uploaded_by, file_path):
    """Send email notification to students about new upload with PDF attachment"""
    try:
        # Get students who want notifications for this specific college, branch, and semester
        students = StudentNotification.objects.filter(
            college=college,
            branch=branch,
            semester=semester,
            wants_notifications=True
        )
        
        if not students.exists():
            return  # No students to notify
        
        # Prepare email content
        doc_type_names = {
            'notes': 'Notes',
            'syllabus': 'Syllabus',
            'midterm': 'Midterm Papers',
            'model': 'Model Papers'
        }
        
        branch_names = {
            'cse': 'Computer Science & Engineering',
            'civil': 'Civil Engineering',
            'auto': 'Automobile Engineering',
            'eee': 'Electrical & Electronics Engineering',
            'ece': 'Electronics & Communication Engineering',
            'ist': 'Information Science & Technology',
            'ice': 'Instrumentation & Control Engineering',
            'mech': 'Mechanical Engineering',
        }
        
        college_names = {
            'meip': 'MEIP',
            'pvp': 'PVP',
            'sjp': 'SJP',
            'rrp': 'RRP',
        }
        
        email_subject = f"📚 New {doc_type_names.get(doc_type)} Uploaded - {branch_names.get(branch)}"
        
        # Create download link
        import os
        download_link = f"http://127.0.0.1:8000/media/{file_path}"
        
        email_message = f"""
Hello Student,

A new document has been uploaded to {college_names.get(college)} College:

📓 Type: {doc_type_names.get(doc_type)}
📝 Title: {title}
📚 Subject: {subject}
🏫 Branch: {branch_names.get(branch)}
📅 Semester: {semester}
👨‍🏫 Uploaded by: {uploaded_by.title()}

📥 Download Link: {download_link}

The PDF is also attached to this email for your convenience.

Happy Learning!
Question Papers Hub Team
        """
        
        # Get list of student emails
        recipient_emails = [student.email for student in students]
        
        # Create email with attachment
        email = EmailMessage(
            subject=email_subject,
            body=email_message,
            from_email=settings.EMAIL_HOST_USER,
            to=recipient_emails,
        )
        
        # Attach PDF if file size is under 5MB
        try:
            file_full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            file_size = os.path.getsize(file_full_path)
            
            # Only attach if under 5MB (5 * 1024 * 1024 bytes)
            if file_size < 5242880:
                with open(file_full_path, 'rb') as f:
                    email.attach(os.path.basename(file_path), f.read(), 'application/pdf')
                print(f"✅ PDF attached to email (Size: {file_size / 1024:.2f} KB)")
            else:
                print(f"⚠️ PDF too large to attach ({file_size / 1024 / 1024:.2f} MB), download link provided")
        except Exception as e:
            print(f"⚠️ Could not attach PDF: {str(e)}")
        
        # Send email
        email.send(fail_silently=True)
        
        print(f"✅ Notification sent to {len(recipient_emails)} students")
        
    except Exception as e:
        print(f"❌ Email notification failed: {str(e)}")


def role_selection_view(request):
    return render(request, 'role_selection.html')


def college_selection_view(request):
    return render(request, 'college_selection.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Generate 6-digit OTP
        otp = OTPVerification.generate_otp()
        
        # Save OTP to database
        OTPVerification.objects.create(email=email, otp=otp)
        
        # Send OTP via email
        try:
            send_mail(
                subject='Your Login OTP',
                message=f'Your OTP for login is: {otp}\n\nThis OTP is valid for 10 minutes.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            
            # Store email in session
            request.session['email'] = email
            messages.success(request, 'OTP sent to your email!')
            return redirect('verify_otp')
        
        except Exception as e:
            messages.error(request, f'Failed to send OTP: {str(e)}')
            return redirect('student_login')
    
    return render(request, 'login.html')


def verify_otp_view(request):
    if 'email' not in request.session:
        messages.error(request, 'Please enter your email first.')
        return redirect('student_login')
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        email = request.session.get('email')
        
        # Get the latest OTP for this email
        try:
            otp_obj = OTPVerification.objects.filter(
                email=email, 
                is_verified=False
            ).latest('created_at')
            
            # Check if OTP is valid and matches
            if otp_obj.is_valid() and otp_obj.otp == entered_otp:
                otp_obj.is_verified = True
                otp_obj.save()
                
                # Clear any existing college/role data
                if 'college' in request.session:
                    del request.session['college']
                if 'college_name' in request.session:
                    del request.session['college_name']
                if 'role' in request.session:
                    del request.session['role']
                if 'branch' in request.session:
                    del request.session['branch']
                if 'branch_name' in request.session:
                    del request.session['branch_name']
                
                # Set user as authenticated in session
                request.session['authenticated'] = True
                request.session['user_email'] = email
                messages.success(request, 'Login successful!')
                return redirect('student_college_selection')
            else:
                if not otp_obj.is_valid():
                    messages.error(request, 'OTP has expired! Please request a new one.')
                else:
                    messages.error(request, 'Invalid OTP! Please try again.')
                return redirect('verify_otp')
        
        except OTPVerification.DoesNotExist:
            messages.error(request, 'No OTP found. Please request a new one.')
            return redirect('student_login')
    
    return render(request, 'verify_otp.html', {'email': request.session.get('email')})


def student_college_selection_view(request):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        messages.error(request, 'Please login first.')
        return redirect('role_selection')
    
    return render(request, 'student_college_selection.html')


def student_select_college_view(request, college):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        messages.error(request, 'Please login first.')
        return redirect('role_selection')
    
    # College names mapping
    college_names = {
        'meip': 'MEIP College',
        'pvp': 'PVP College',
        'sjp': 'SJP College',
        'rrp': 'RRP College',
    }
    
    # Store college in session
    request.session['college'] = college
    request.session['college_name'] = college_names.get(college, 'College')
    request.session['role'] = 'student'
    
    # Clear previous college registrations when switching colleges
    email = request.session.get('user_email')
    if email:
        # Remove all previous registrations for this student
        StudentNotification.objects.filter(email=email).delete()
    
    messages.success(request, f'Welcome to {college_names.get(college)}!')
    return redirect('branch_selection')


def teacher_login_view(request, college):
    # College names mapping
    college_names = {
        'meip': 'MEIP College',
        'pvp': 'PVP College',
        'sjp': 'SJP College',
        'rrp': 'RRP College',
    }
    
    college_name = college_names.get(college, 'College')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Teacher credentials with their branches and colleges
        TEACHERS = {
            'krishna': {'password': '1234', 'branch': 'ist', 'branch_name': 'Information Science & Technology', 'college': 'pvp'},
            'rajesh': {'password': '5678', 'branch': 'cse', 'branch_name': 'Computer Science & Engineering', 'college': 'meip'},
            'priya': {'password': 'civil123', 'branch': 'civil', 'branch_name': 'Civil Engineering', 'college': 'sjp'},
            'arjun': {'password': 'auto456', 'branch': 'auto', 'branch_name': 'Automobile Engineering', 'college': 'pvp'},
            'lakshmi': {'password': 'eee789', 'branch': 'eee', 'branch_name': 'Electrical & Electronics Engineering', 'college': 'rrp'},
            'suresh': {'password': 'ece321', 'branch': 'ece', 'branch_name': 'Electronics & Communication Engineering', 'college': 'meip'},
            'kavya': {'password': 'ice654', 'branch': 'ice', 'branch_name': 'Instrumentation & Control Engineering', 'college': 'sjp'},
            'vikram': {'password': 'mech987', 'branch': 'mech', 'branch_name': 'Mechanical Engineering', 'college': 'rrp'},
        }
        
        if username in TEACHERS and TEACHERS[username]['password'] == password:
            teacher_data = TEACHERS[username]
            
            # Check if teacher belongs to this college
            if teacher_data['college'] != college:
                messages.error(request, f'You are not authorized to login to {college_name}!')
                return redirect('teacher_login_college', college=college)
            
            request.session['authenticated'] = True
            request.session['user_email'] = username
            request.session['role'] = 'teacher'
            request.session['branch'] = teacher_data['branch']
            request.session['branch_name'] = teacher_data['branch_name']
            request.session['college'] = college
            request.session['college_name'] = college_name
            messages.success(request, f'Welcome {username.title()}!')
            return redirect('teacher_dashboard', branch=teacher_data['branch'])
        else:
            messages.error(request, 'Invalid username or password!')
            return redirect('teacher_login_college', college=college)
    
    return render(request, 'teacher_login.html', {'college': college, 'college_name': college_name})


def branch_selection_view(request):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        messages.error(request, 'Please login first.')
        return redirect('role_selection')
    
    # Check if college is selected (for students)
    if request.session.get('role') != 'teacher' and not request.session.get('college'):
        messages.error(request, 'Please select your college first.')
        return redirect('student_college_selection')
    
    return render(request, 'branch_selection.html')


def semester_selection_view(request, branch):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        messages.error(request, 'Please login first.')
        return redirect('role_selection')
    
    # Branch names mapping
    branch_names = {
        'cse': 'Computer Science & Engineering',
        'civil': 'Civil Engineering',
        'auto': 'Automobile Engineering',
        'eee': 'Electrical & Electronics Engineering',
        'ece': 'Electronics & Communication Engineering',
        'ist': 'Information Science & Technology',
        'ice': 'Instrumentation & Control Engineering',
        'mech': 'Mechanical Engineering',
    }
    
    branch_name = branch_names.get(branch, 'Unknown Branch')
    
    return render(request, 'semester_selection.html', {
        'branch': branch,
        'branch_name': branch_name
    })


def teacher_dashboard_view(request, branch):
    # Check if user is authenticated and is a teacher
    if not request.session.get('authenticated') or request.session.get('role') != 'teacher':
        messages.error(request, 'Please login as teacher first.')
        return redirect('teacher_login')
    
    # Check if teacher belongs to this branch
    if request.session.get('branch') != branch:
        messages.error(request, 'You do not have access to this branch.')
        return redirect('teacher_login')
    
    teacher_name = request.session.get('user_email', 'Teacher').title()
    branch_name = request.session.get('branch_name', 'Unknown Branch')
    
    return render(request, 'teacher_dashboard.html', {
        'teacher_name': teacher_name,
        'branch': branch,
        'branch_name': branch_name
    })


def upload_notes_view(request, branch, semester):
    # Check if user is authenticated and is a teacher
    if not request.session.get('authenticated') or request.session.get('role') != 'teacher':
        messages.error(request, 'Please login as teacher first.')
        return redirect('teacher_login')
    
    # Check if teacher belongs to this branch
    if request.session.get('branch') != branch:
        messages.error(request, 'You do not have access to this branch.')
        return redirect('teacher_login')
    
    branch_name = request.session.get('branch_name', 'Unknown Branch')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        year = request.POST.get('year')
        file = request.FILES.get('file')
        uploaded_by = request.session.get('user_email')
        
        # Create new question paper entry
        QuestionPaper.objects.create(
            branch=branch,
            semester=semester,
            title=title,
            subject=subject,
            year=year,
            uploaded_by=uploaded_by,
            file=file
        )
        
        messages.success(request, 'Question paper uploaded successfully!')
        return redirect('teacher_dashboard', branch=branch)
    
    return render(request, 'upload_notes.html', {
        'branch': branch,
        'branch_name': branch_name,
        'semester': semester
    })


def select_semester_upload_view(request, branch):
    # Check if user is authenticated and is a teacher
    if not request.session.get('authenticated') or request.session.get('role') != 'teacher':
        messages.error(request, 'Please login as teacher first.')
        return redirect('teacher_login')
    
    # Check if teacher belongs to this branch
    if request.session.get('branch') != branch:
        messages.error(request, 'You do not have access to this branch.')
        return redirect('teacher_login')
    
    branch_name = request.session.get('branch_name', 'Unknown Branch')
    
    return render(request, 'select_semester_upload.html', {
        'branch': branch,
        'branch_name': branch_name
    })


def upload_type_selection_view(request, branch, semester):
    # Check if user is authenticated and is a teacher
    if not request.session.get('authenticated') or request.session.get('role') != 'teacher':
        messages.error(request, 'Please login as teacher first.')
        return redirect('teacher_login')
    
    # Check if teacher belongs to this branch
    if request.session.get('branch') != branch:
        messages.error(request, 'You do not have access to this branch.')
        return redirect('teacher_login')
    
    branch_name = request.session.get('branch_name', 'Unknown Branch')
    
    return render(request, 'upload_type_selection.html', {
        'branch': branch,
        'semester': semester,
        'branch_name': branch_name
    })


def upload_document_view(request, branch, semester, doc_type):
    # Check if user is authenticated and is a teacher
    if not request.session.get('authenticated') or request.session.get('role') != 'teacher':
        messages.error(request, 'Please login as teacher first.')
        return redirect('teacher_login')
    
    # Check if teacher belongs to this branch
    if request.session.get('branch') != branch:
        messages.error(request, 'You do not have access to this branch.')
        return redirect('teacher_login')
    
    branch_name = request.session.get('branch_name', 'Unknown Branch')
    
    # Document type names
    doc_type_names = {
        'notes': 'Notes',
        'syllabus': 'Syllabus',
        'midterm': 'Midterm Papers',
        'model': 'Model Papers'
    }
    
    doc_type_name = doc_type_names.get(doc_type, 'Document')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        year = request.POST.get('year')
        file = request.FILES.get('file')
        uploaded_by = request.session.get('user_email')
        
        # Create new question paper entry
        paper = QuestionPaper.objects.create(
            branch=branch,
            college=request.session.get('college'),
            semester=semester,
            doc_type=doc_type,
            title=title,
            subject=subject,
            year=year,
            uploaded_by=uploaded_by,
            file=file
        )
        
        # Send notification to students
        send_upload_notification(
            college=request.session.get('college'),
            branch=branch,
            semester=semester,
            doc_type=doc_type,
            title=title,
            subject=subject,
            uploaded_by=uploaded_by,
            file_path=paper.file.name
        )
        
        messages.success(request, f'{doc_type_name} uploaded successfully!')
        return redirect('teacher_dashboard', branch=branch)
    
    return render(request, 'upload_notes.html', {
        'branch': branch,
        'branch_name': branch_name,
        'semester': semester,
        'doc_type_name': doc_type_name
    })


def manage_papers_view(request, branch):
    # Check if user is authenticated and is a teacher
    if not request.session.get('authenticated') or request.session.get('role') != 'teacher':
        messages.error(request, 'Please login as teacher first.')
        return redirect('teacher_login')
    
    # Check if teacher belongs to this branch
    if request.session.get('branch') != branch:
        messages.error(request, 'You do not have access to this branch.')
        return redirect('teacher_login')
    
    branch_name = request.session.get('branch_name', 'Unknown Branch')
    uploaded_by = request.session.get('user_email')
    
    # Get all papers uploaded by this teacher
    papers = QuestionPaper.objects.filter(
        branch=branch, 
        uploaded_by=uploaded_by,
        college=request.session.get('college')
    )
    
    return render(request, 'manage_papers.html', {
        'branch': branch,
        'branch_name': branch_name,
        'papers': papers
    })


def delete_paper_view(request, paper_id):
    # Check if user is authenticated and is a teacher
    if not request.session.get('authenticated') or request.session.get('role') != 'teacher':
        messages.error(request, 'Please login as teacher first.')
        return redirect('teacher_login')
    
    if request.method == 'POST':
        try:
            paper = QuestionPaper.objects.get(id=paper_id, uploaded_by=request.session.get('user_email'))
            branch = paper.branch
            
            # Delete the file from storage
            if paper.file:
                paper.file.delete()
            
            # Delete the database entry
            paper.delete()
            messages.success(request, 'Paper deleted successfully!')
        except QuestionPaper.DoesNotExist:
            messages.error(request, 'Paper not found or you do not have permission to delete it.')
        
        return redirect('manage_papers', branch=branch)
    
    return redirect('teacher_dashboard', branch=request.session.get('branch'))


def view_notes_view(request, branch, semester):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        messages.error(request, 'Please login first.')
        return redirect('role_selection')
    
    # Branch names mapping
    branch_names = {
        'cse': 'Computer Science & Engineering',
        'civil': 'Civil Engineering',
        'auto': 'Automobile Engineering',
        'eee': 'Electrical & Electronics Engineering',
        'ece': 'Electronics & Communication Engineering',
        'ist': 'Information Science & Technology',
        'ice': 'Instrumentation & Control Engineering',
        'mech': 'Mechanical Engineering',
    }
    
    branch_name = branch_names.get(branch, 'Unknown Branch')
    
    # Get all papers for this branch and semester
    # Filter by college for both students and teachers
    papers = QuestionPaper.objects.filter(
        branch=branch, 
        semester=semester,
        college=request.session.get('college')
    )
    
    # Track that this student viewed this branch/semester (for smart notifications)
    email = request.session.get('user_email')
    college = request.session.get('college')
    if email and college and request.session.get('role') != 'teacher':
        # Update or create student notification preference for this specific branch/semester
        StudentNotification.objects.update_or_create(
            email=email,
            college=college,
            branch=branch,
            semester=semester,
            defaults={'wants_notifications': True}
        )
    
    return render(request, 'view_notes.html', {
        'branch': branch,
        'semester': semester,
        'branch_name': branch_name,
        'papers': papers
    })
def internships_view(request, branch):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        messages.error(request, 'Please login first.')
        return redirect('role_selection')
    
    # Only show internships for CSE, IST, and MECH branches
    if branch not in ['cse', 'ist', 'mech', 'civil', 'eee', 'ece', 'auto', 'ice']:
        messages.error(request, 'Internships are only available for CSE, ISE, and Mechanical branches.')
        return redirect('semester_selection', branch=branch)
    
    # Branch names mapping
    branch_names = {
        'cse': 'Computer Science & Engineering',
        'ist': 'Information Science & Technology',
        'mech': 'Mechanical Engineering',
        'civil' : 'Civil Engineering',
        'eee' : 'Electrical & Electronics Engineering',
        'ece' : 'Electronics & Communication Engineering',
        'auto' : 'Automobile Engineering',
        'ice': 'Instrumentation & Control Engineering',
    }
    
    branch_name = branch_names.get(branch, 'Unknown Branch')
    
    # CSE and IST internships
    cse_ist_internships = [
        {
            'company_name': 'Scontinent Technology',
            'role': 'Full Stack Developer Intern',
            'logo_initials': 'SC',
            'location': 'Bangalore (Hybrid)',
            'duration': '6 Months',
            'description': 'Work on real-world projects using Python, Django, and React',
            'skills': ['Python', 'Django', 'React', 'SQL'],
            'apply_link': 'https://scontinent.com',
        },
        {
            'company_name': 'KaaShiv Infotech',
            'role': 'Software Development Intern',
            'logo_initials': 'KI',
            'location': 'Chennai (On-site)',
            'duration': '3-6 Months',
            'description': 'Learn software development with hands-on training',
            'skills': ['Java', 'PHP', 'Web Development'],
            'apply_link': 'https://www.kaashivinfotech.com',
        },
        {
            'company_name': 'ThinkNEXT Technologies',
            'role': 'Web Development Intern',
            'logo_initials': 'TN',
            'location': 'Chandigarh/Online',
            'duration': '1-6 Months',
            'description': 'Learn modern web technologies',
            'skills': ['HTML/CSS', 'JavaScript', 'PHP'],
            'apply_link': 'https://www.thinknexttraining.com',
        },
        {
            'company_name': 'Internshala',
            'role': 'Various Tech Internships',
            'logo_initials': 'IS',
            'location': 'Multiple Locations/Remote',
            'duration': 'Varies',
            'description': 'Platform with 800+ internships for diploma students',
            'skills': ['Multiple Skills', 'Remote Options'],
            'apply_link': 'https://internshala.com',
        },
        {
            'company_name': 'InternshipWala',
            'role': 'CSE Online Internships',
            'logo_initials': 'IW',
            'location': 'Online/Remote',
            'duration': '2-3 Months',
            'description': 'Online certificate programs in various tech domains',
            'skills': ['Python', 'Data Science', 'Cyber Security'],
            'apply_link': 'https://www.internshipwala.com',
        },
        {
            'company_name': 'Innovians Technologies',
            'role': 'Summer Internship Program',
            'logo_initials': 'IT',
            'location': 'Multiple Cities/Online',
            'duration': '2-8 Weeks',
            'description': 'Hands-on training in emerging technologies',
            'skills': ['IoT', 'Machine Learning', 'Web Dev'],
            'apply_link': 'https://innovianstechnologies.com',
        },
        {
            'company_name': 'Optimspace.in',
            'role': 'Data Science Intern',
            'logo_initials': 'OP',
            'location': 'Remote',
            'duration': '3 Months',
            'description': 'Learn data science and AI fundamentals',
            'skills': ['Data Science', 'AI', 'Python'],
            'apply_link': 'https://optimspace.in',
        },
        {
            'company_name': 'Wellorgs Infotech',
            'role': 'Computer Vision Intern',
            'logo_initials': 'WI',
            'location': 'Bangalore (Hybrid)',
            'duration': '3-6 Months',
            'description': 'Work on computer vision and image processing projects',
            'skills': ['Computer Vision', 'OpenCV', 'Python'],
            'apply_link': 'https://wellorgs.com/',
        },
        {
            'company_name': 'Quaere e-Technologies',
            'role': 'Software Development Intern',
            'logo_initials': 'QE',
            'location': 'Hyderabad (On-site)',
            'duration': '6 Months',
            'description': 'Full-stack development training program',
            'skills': ['Java', 'SQL', 'Cloud'],
            'apply_link': 'https://www.quaeretech.com/Careers',
        },
        {
            'company_name': 'DIPC Tech',
            'role': 'IoT Development Intern',
            'logo_initials': 'DT',
            'location': 'Pune (On-site)',
            'duration': '3-6 Months',
            'description': 'Learn IoT development with hands-on projects',
            'skills': ['Arduino', 'Raspberry Pi', 'C++'],
            'apply_link': 'https://dipc.tech/',
        },
    ]
    
    # Mechanical Engineering internships
    mech_internships = [
        {
            'company_name': 'ThinkNEXT Technologies',
            'role': 'Mechanical Engineering Intern',
            'logo_initials': 'TN',
            'location': 'Online/Offline',
            'duration': '1-6 Months',
            'description': 'Mechanical engineering internships (CAD/CAM, CNC programming, HVAC, Design)',
            'skills': ['CAD/CAM', 'CNC', 'HVAC', 'Design'],
            'apply_link': 'https://www.thinknexttraining.com',
        },
        {
            'company_name': 'Igeeks Technologies',
            'role': 'Mechanical Internship',
            'logo_initials': 'IG',
            'location': 'Offline/Onsite',
            'duration': 'Varies',
            'description': 'Hands-on practical internship for CAD, modelling, design work',
            'skills': ['CAD', 'Modelling', 'Design'],
            'apply_link': 'https://igeekstechnologies.com/',
        },
        {
            'company_name': 'SMEClabs',
            'role': 'Mechanical Engineering Training',
            'logo_initials': 'SM',
            'location': 'Offline',
            'duration': 'Short/Long term',
            'description': 'Training programs for Engineering, Diploma, Degree students',
            'skills': ['Manufacturing', 'Design', 'Analysis'],
            'apply_link': 'https://www.smeclabs.com/',
        },
        {
            'company_name': 'Emertxe',
            'role': 'Embedded Systems Intern',
            'logo_initials': 'EM',
            'location': 'Online',
            'duration': 'Varies',
            'description': 'Embedded Systems / IoT internships for mechanical students',
            'skills': ['Embedded Systems', 'IoT', 'Automation'],
            'apply_link': 'https://www.emertxe.com/',
        },
        {
            'company_name': 'NTTF',
            'role': 'Manufacturing & Mechatronics Intern',
            'logo_initials': 'NT',
            'location': 'Offline/Workshop',
            'duration': '4 Weeks',
            'description': 'CADD, CNC, Mechatronics, Automation, 3D printing programs',
            'skills': ['CNC', 'Mechatronics', '3D Printing'],
            'apply_link': 'https://nttftrg.com/',
        },
        {
            'company_name': 'KaaShiv Infotech',
            'role': 'Mechanical/Diploma Internship',
            'logo_initials': 'KI',
            'location': 'Online/Offline',
            'duration': 'Varies',
            'description': 'Project-based internships with reports and certificates',
            'skills': ['CAD', 'Analysis', 'Projects'],
            'apply_link': 'https://www.kaashivinfotech.com',
        },
        {
            'company_name': 'Skill-Lync',
            'role': 'CAD/CAE Training',
            'logo_initials': 'SL',
            'location': 'Online',
            'duration': '2-6 Months',
            'description': 'Industry-oriented CAD, CAE, and CFD training',
            'skills': ['CAD', 'CAE', 'CFD', 'ANSYS'],
            'apply_link': 'https://skill-lync.com/',
        },
        {
            'company_name': 'CADD Centre',
            'role': 'Design & Drafting Intern',
            'logo_initials': 'CC',
            'location': 'Multiple Cities',
            'duration': '3-6 Months',
            'description': 'AutoCAD, SolidWorks, and manufacturing design training',
            'skills': ['AutoCAD', 'SolidWorks', 'CATIA'],
            'apply_link': 'https://caddcentre.com/',
        },
        {
            'company_name': 'TATA Technologies',
            'role': 'Product Design Intern',
            'logo_initials': 'TT',
            'location': 'Pune/Bangalore',
            'duration': '6 Months',
            'description': 'Work on automotive and aerospace design projects',
            'skills': ['Product Design', 'CAD', 'Simulation'],
            'apply_link': 'https://www.tata.com/careers/programs/tata-global-internships/apply-here',
        },
        {
            'company_name': 'L&T Construction',
            'role': 'Site Engineering Intern',
            'logo_initials': 'LT',
            'location': 'Various Sites',
            'duration': '3-6 Months',
            'description': 'On-site mechanical engineering and construction management',
            'skills': ['Construction', 'Project Management', 'MEP'],
            'apply_link': 'https://www.lntecc.com/',
        },
    ]
    #Civil Engineering
    civil_internships = [
        {
            'company_name': 'ThinkNEXT Technologies',
            'role': 'Civil Engineering Intern',
            'logo_initials': 'TN',
            'location': 'Online/Offline',
            'duration': '1-6 Months',
            'description': 'Hands-on civil engineering internship — project support, field basics, documentation, CAD drafting & site exposure.',
            'skills': ['AutoCAD', 'Site Surveying', 'Construction Planning', 'Quantity Estimation', 'BOQ Preparation'],
            'apply_link': 'https://www.thinknexttraining.com/Internship-in-civil-engineering-students.aspx',
        },
        {
            'company_name': 'CivilEra',
            'role': 'Civil Engineering Intern',
            'logo_initials': 'CE',
            'location': 'Online/Offline',
            'duration': '1-6 Months',
            'description': 'Internship with real projects in structural & civil works, including software training & project reporting. Covers construction methodologies and design basics. Offers certificates.',
            'skills': ['ETABS', 'STAAD Pro', 'Safe', 'Revit Structures', 'AutoCAD', 'Project Management'],
            'apply_link': 'https://www.civilera.com/interns',
        },
        {
            'company_name': 'Internshala',
            'role': 'Civil Engineering Intern',
            'logo_initials': 'IH',
            'location': 'Online/Offline (varies by posting)',
            'duration': '1-6 Months',
            'description': 'Platform aggregating civil internships across Bengaluru. Roles involve site assistance, drafting, estimation, CAD modelling, reporting.',
            'skills': ['AutoCAD', 'Site Assistance', 'Quantity Surveying', 'MS Excel', 'Report Writing'],
            'apply_link': 'https://internshala.com/internships/civil-internship-in-bangalore',
        },
        {
            'company_name': 'Sanfoundry',
            'role': 'Civil Engineering Intern',
            'logo_initials': 'SF',
            'location': 'Work From Home / Office Bangalore',
            'duration': '1-3 Months',
            'description': 'Remote or office internships including civil engineering project contributions, learning and documentation tasks.',
            'skills': ['Technical Writing', 'Civil Concepts', 'Problem Solving', 'Project Research'],
            'apply_link': 'https://www.sanfoundry.com/internship/',
        },
        {
            'company_name': 'Practice School (via practiceschool.in)',
            'role': 'Civil Engineering Intern',
            'logo_initials': 'PS',
            'location': 'Online/Offline',
            'duration': '1-6 Months',
            'description': 'Internships with flexible options including AutoCAD & STAAD Pro, construction exposure, field planning, and certification support.',
            'skills': ['AutoCAD', 'STAAD Pro', 'Site Monitoring', 'Construction Methods', 'Team Collaboration'],
            'apply_link': 'https://practiceschool.in/engineering-in-civil/',
        },
        {
            'company_name': 'Local Construction/Consultancy Firms (via Internshala/LinkedIn)',
            'role': 'Civil Engineering Intern',
            'logo_initials': 'LC',
            'location': 'Offline',
            'duration': '1-6 Months',
            'description': 'Internship with Bangalore-based contractors & consultants (site work, supervision, documentation, quantity surveying). Apply via listings.',
            'skills': ['Site Supervision', 'Material Testing', 'Surveying', 'Concrete & Soil Basics', 'Field Reports'],
            'apply_link': 'https://internshala.com/internships/civil-internship-in-bangalore',
        },
        {
            'company_name': 'Burns & McDonnell India',
            'role': 'Civil Trainee Engineer / Intern',
            'logo_initials': 'BM',
            'location': 'Offline (Bengaluru)',
            'duration': '3-6 Months',
            'description': 'Trainee internship focusing on drafting, design calculations, construction documentation under a well-known engineering firm. (Civil roles appear on listings.)',
            'skills': ['Civil Drafting', 'Documentation', 'Structural Basics', 'Revit/AutoCAD', 'Team Coordination'],
            'apply_link': 'https://www.glassdoor.co.in/Job/bangalore-civil-engineering-internship-jobs-SRCH_IL.0,9_IM1091_KO10,38.htm',
        },
        {
            'company_name': 'LinkedIn Civil Intern Roles (Various Employers)',
            'role': 'Civil Engineering Intern',
            'logo_initials': 'LI',
            'location': 'Offline/Hybrid (varies)',
            'duration': '1-6 Months',
            'description': 'Multiple civil internships in Bangalore listed by employers on LinkedIn (site assistant, design support, surveying). You can apply directly via LinkedIn.',
            'skills': ['AutoCAD', 'Site Coordination', 'MS Excel', 'Basic Design', 'Reporting'],
            'apply_link': 'https://www.linkedin.com/jobs/civil-engineering-intern-jobs-bengaluru',
        },
        {
            'company_name': 'InternshipWala (Civil Internships)',
            'role': 'Civil Engineering Intern',
            'logo_initials': 'IW',
            'location': 'Online/Offline',
            'duration': '1-8 Weeks (varies)',
            'description': 'Civil internships in areas like roads & highways, building construction, STAAD Pro & AutoCAD work; often online projects & reports.',
            'skills': ['AutoCAD', 'STAAD Pro', 'Roads & Highways Concepts', 'Construction Workflow', 'Reporting'],
            'apply_link': 'https://www.internshipwala.com/CivilEngineering-Internship',
        },
    ]
    eee_internship = [
        {
        'company_name': 'ThinkNEXT Technologies',
        'role': 'Electrical & Electronics Engineering Intern',
        'logo_initials': 'TN',
        'location': 'Online/Offline',
        'duration': '1-6 Months',
        'description': 'Internship for EEE/ECE students covering industrial automation, power systems, embedded systems, PLC/SCADA, wiring, control systems and more, with hands-on exposure. Offers certificates and industry support. ',
        'skills': ['PLC', 'SCADA', 'Power Systems', 'Embedded Systems', 'Electrical Wiring', 'Control Systems'],
        'apply_link': 'https://www.thinknexttraining.com/internship-in-electrical-engineering.aspx',
        },
        {
        'company_name': 'KaaShiv Infotech',
        'role': 'EEE/Electronics Engineering Intern',
        'logo_initials': 'KI',
        'location': 'Online/Offline (Bangalore & other cities)',
        'duration': '1-6 Months',
        'description': 'Internship/training for EEE/ECE students including embedded tech, MATLAB, signal processing, IoT, power electronics, robotics, and hardware basics; certificate provided. ',
        'skills': ['Embedded Systems', 'MATLAB', 'Signal Processing', 'IoT', 'Power Electronics', 'Robotics'],
        'apply_link': 'https://www.kaashivinfotech.com/eee-internship-in-bangalore/',
        },
        {
        'company_name': 'Indian Institute of Embedded Systems (IIES)',
        'role': 'Embedded Systems & Electronics Intern',
        'logo_initials': 'II',
        'location': 'Online/Offline (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Internship focused on embedded systems, firmware design, microcontroller programming, IoT and VLSI fundamentals. Offers certificates and project experience. ',
        'skills': ['Embedded C/C++', 'Microcontrollers (ARM/8051)', 'Firmware Development', 'IoT', 'Hardware Testing'],
        'apply_link': 'https://iies.in/vlsi-and-embedded-internship/',
        },
        {
        'company_name': 'Internshala (Electronics & Electrical Internships)',
        'role': 'Electrical/Electronics Engineering Intern',
        'logo_initials': 'IN',
        'location': 'Online/Offline (Various Companies in Bangalore)',
        'duration': 'Varies by Role',
        'description': 'Platform listing multiple electrical & electronics internships (work-from-home, remote & onsite) with roles across power systems, circuits, hardware support, testing and more. ',
        'skills': ['Circuit Analysis', 'Power Electronics', 'Hardware Testing', 'Documentation', 'MS Excel'],
        'apply_link': 'https://internshala.com/internships/electronics-internship-in-bangalore',
        },
        {
        'company_name': 'Infidata Technologies',
        'role': 'Electrical & Electronics Intern',
        'logo_initials': 'IT',
        'location': 'Offline/Online (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Engineering internship for diploma/B.Tech students including real-world electrical/electronics tech experience and industry guidance (certificate provided). ',
        'skills': ['Circuit Design', 'PCB Basics', 'Electrical Systems', 'Technical Reporting', 'Team Collaboration'],
        'apply_link': 'https://infidata.in/internship-in-bangalore.php',
        },
        {
        'company_name': 'Technofist',
        'role': 'Electrical/Electronics Engineering Intern',
        'logo_initials': 'TF',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-4 Months',
        'description': 'Internship in electrical and electronics domain including embedded systems fundamentals, microcontrollers, IoT, MATLAB and hardware basics. ',
        'skills': ['Embedded C', 'Electrical Fundamentals', 'MATLAB', 'IoT Applications', 'Microcontrollers'],
        'apply_link': 'https://www.technofist.com/electricals_internship.html',
        },
        {
        'company_name': 'ONLEI Technologies',
        'role': 'Electrical & Electronics Intern',
        'logo_initials': 'OT',
        'location': 'Online/Offline (India)',
        'duration': '1-3 Months',
        'description': 'Internship/training for ECE & EEE students covering Python, machine learning, IoT, CCNA, robotics and more blended with electrical systems basics. ',
        'skills': ['Python', 'Machine Learning', 'IoT', 'Robotics', 'CCNA'],
        'apply_link': 'https://onleitechnologies.com/internships-for-ece-students-and-eee-students/',
        },
        {
        'company_name': 'StartAutomation.in',
        'role': 'Industrial Automation/Electrical Intern',
        'logo_initials': 'SA',
        'location': 'Offline/Bangalore',
        'duration': '1-6 Months',
        'description': 'Internship focused on industrial automation, controls, electrical system fundamentals and practical systems exposure in automation contexts. ',
        'skills': ['Industrial Automation', 'PLC/HMI Basics', 'Electrical Controls', 'Circuit Analysis', 'Field Testing'],
        'apply_link': 'https://www.startautomation.in/internship.html',
        },
        {
        'company_name': 'Astrome Technologies (via Internshala/LinkedIn)',
        'role': 'Electronics/Hardware Intern',
        'logo_initials': 'AT',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Internship in electronics hardware, system testing, embedded applications and prototype design (apply via portal listings). ',
        'skills': ['Hardware Design', 'Embedded Firmware', 'Testing & Validation', 'Circuit Debugging', 'Documentation'],
        'apply_link': 'https://internshala.com/internships/electronics-internship-in-bangalore',
        },
        {
        'company_name': 'Medetronix (via LinkedIn)',
        'role': 'Electronics Engineering Intern',
        'logo_initials': 'MX',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Electronics internship with roles around system architecture, embedded design, testing and analysis — entry level for students (apply via LinkedIn). ',
        'skills': ['System Architecture', 'Embedded Tools', 'Test Engineering', 'Signal Processing', 'Documentation'],
        'apply_link': 'https://www.linkedin.com/jobs/electronics-internship-jobs-bengaluru',
        },
        {
        'company_name': 'LinkedIn/Burns & McDonnell India (Electrical Intern Roles)',
        'role': 'Electrical Engineering Intern',
        'logo_initials': 'BM',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Engineering internship roles with exposure to power systems, substation support, electrical design and field engineering (positions found on LinkedIn). ',
        'skills': ['Power Systems', 'Electrical Design', 'Safety Standards', 'Project Support', 'Field Testing'],
        'apply_link': 'https://in.linkedin.com/jobs/electrical-engineering-intern-jobs-bengaluru',
        },
    ]
    ece_internship = [
        {
        'company_name': 'ThinkNEXT Technologies',
        'role': 'Electrical & Electronics Engineering Intern',
        'logo_initials': 'TN',
        'location': 'Online/Offline',
        'duration': '1-6 Months',
        'description': 'Internship for EEE/ECE students covering industrial automation, power systems, embedded systems, PLC/SCADA, wiring, control systems and more, with hands-on exposure. Offers certificates and industry support. ',
        'skills': ['PLC', 'SCADA', 'Power Systems', 'Embedded Systems', 'Electrical Wiring', 'Control Systems'],
        'apply_link': 'https://www.thinknexttraining.com/internship-in-electrical-engineering.aspx',
        },
        {
        'company_name': 'KaaShiv Infotech',
        'role': 'EEE/Electronics Engineering Intern',
        'logo_initials': 'KI',
        'location': 'Online/Offline (Bangalore & other cities)',
        'duration': '1-6 Months',
        'description': 'Internship/training for EEE/ECE students including embedded tech, MATLAB, signal processing, IoT, power electronics, robotics, and hardware basics; certificate provided. ',
        'skills': ['Embedded Systems', 'MATLAB', 'Signal Processing', 'IoT', 'Power Electronics', 'Robotics'],
        'apply_link': 'https://www.kaashivinfotech.com/eee-internship-in-bangalore/',
        },
        {
        'company_name': 'Indian Institute of Embedded Systems (IIES)',
        'role': 'Embedded Systems & Electronics Intern',
        'logo_initials': 'II',
        'location': 'Online/Offline (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Internship focused on embedded systems, firmware design, microcontroller programming, IoT and VLSI fundamentals. Offers certificates and project experience. ',
        'skills': ['Embedded C/C++', 'Microcontrollers (ARM/8051)', 'Firmware Development', 'IoT', 'Hardware Testing'],
        'apply_link': 'https://iies.in/vlsi-and-embedded-internship/',
        },
        {
        'company_name': 'Internshala (Electronics & Electrical Internships)',
        'role': 'Electrical/Electronics Engineering Intern',
        'logo_initials': 'IN',
        'location': 'Online/Offline (Various Companies in Bangalore)',
        'duration': 'Varies by Role',
        'description': 'Platform listing multiple electrical & electronics internships (work-from-home, remote & onsite) with roles across power systems, circuits, hardware support, testing and more. ',
        'skills': ['Circuit Analysis', 'Power Electronics', 'Hardware Testing', 'Documentation', 'MS Excel'],
        'apply_link': 'https://internshala.com/internships/electronics-internship-in-bangalore',
        },
        {
        'company_name': 'Infidata Technologies',
        'role': 'Electrical & Electronics Intern',
        'logo_initials': 'IT',
        'location': 'Offline/Online (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Engineering internship for diploma/B.Tech students including real-world electrical/electronics tech experience and industry guidance (certificate provided). ',
        'skills': ['Circuit Design', 'PCB Basics', 'Electrical Systems', 'Technical Reporting', 'Team Collaboration'],
        'apply_link': 'https://infidata.in/internship-in-bangalore.php',
        },
        {
        'company_name': 'Technofist',
        'role': 'Electrical/Electronics Engineering Intern',
        'logo_initials': 'TF',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-4 Months',
        'description': 'Internship in electrical and electronics domain including embedded systems fundamentals, microcontrollers, IoT, MATLAB and hardware basics. ',
        'skills': ['Embedded C', 'Electrical Fundamentals', 'MATLAB', 'IoT Applications', 'Microcontrollers'],
        'apply_link': 'https://www.technofist.com/electricals_internship.html',
        },
        {
        'company_name': 'ONLEI Technologies',
        'role': 'Electrical & Electronics Intern',
        'logo_initials': 'OT',
        'location': 'Online/Offline (India)',
        'duration': '1-3 Months',
        'description': 'Internship/training for ECE & EEE students covering Python, machine learning, IoT, CCNA, robotics and more blended with electrical systems basics. ',
        'skills': ['Python', 'Machine Learning', 'IoT', 'Robotics', 'CCNA'],
        'apply_link': 'https://onleitechnologies.com/internships-for-ece-students-and-eee-students/',
        },
        {
        'company_name': 'StartAutomation.in',
        'role': 'Industrial Automation/Electrical Intern',
        'logo_initials': 'SA',
        'location': 'Offline/Bangalore',
        'duration': '1-6 Months',
        'description': 'Internship focused on industrial automation, controls, electrical system fundamentals and practical systems exposure in automation contexts. ',
        'skills': ['Industrial Automation', 'PLC/HMI Basics', 'Electrical Controls', 'Circuit Analysis', 'Field Testing'],
        'apply_link': 'https://www.startautomation.in/internship.html',
        },
        {
        'company_name': 'Astrome Technologies (via Internshala/LinkedIn)',
        'role': 'Electronics/Hardware Intern',
        'logo_initials': 'AT',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Internship in electronics hardware, system testing, embedded applications and prototype design (apply via portal listings). ',
        'skills': ['Hardware Design', 'Embedded Firmware', 'Testing & Validation', 'Circuit Debugging', 'Documentation'],
        'apply_link': 'https://internshala.com/internships/electronics-internship-in-bangalore',
        },
        {
        'company_name': 'Medetronix (via LinkedIn)',
        'role': 'Electronics Engineering Intern',
        'logo_initials': 'MX',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Electronics internship with roles around system architecture, embedded design, testing and analysis — entry level for students (apply via LinkedIn). ',
        'skills': ['System Architecture', 'Embedded Tools', 'Test Engineering', 'Signal Processing', 'Documentation'],
        'apply_link': 'https://www.linkedin.com/jobs/electronics-internship-jobs-bengaluru',
        },
        {
        'company_name': 'LinkedIn/Burns & McDonnell India (Electrical Intern Roles)',
        'role': 'Electrical Engineering Intern',
        'logo_initials': 'BM',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Engineering internship roles with exposure to power systems, substation support, electrical design and field engineering (positions found on LinkedIn). ',
        'skills': ['Power Systems', 'Electrical Design', 'Safety Standards', 'Project Support', 'Field Testing'],
        'apply_link': 'https://in.linkedin.com/jobs/electrical-engineering-intern-jobs-bengaluru',
        },
    ]
    auto_internship = [
        {
        'company_name': 'Volvo Group India Pvt. Ltd.',
        'role': 'Automobile Engineering Intern (Spark Intern Program)',
        'logo_initials': 'VG',
        'location': 'Offline (Bangalore)',
        'duration': 'Up to 9 Months',
        'description': 'Internship in automotive engineering with exposure to transport solutions, vehicle systems, prototyping, and industry projects. Opportunity for hands-on learning and professional growth. Mentioned as open in Bangalore. ',
        'skills': ['Vehicle Systems', 'Automotive Design', 'Prototyping', 'CAD', 'Team Collaboration'],
        'apply_link': 'https://jobs.volvogroup.com',
        },
        {
        'company_name': 'Ather Energy',
        'role': 'Automobile & EV Engineering Intern',
        'logo_initials': 'AE',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '3-6 Months',
        'description': 'Internship focusing on electric vehicle technology, motor control, battery systems, and product innovation for electric scooters and vehicles. Good for EV-oriented automobile roles. ',
        'skills': ['EV Systems', 'Battery Tech', 'Motor Control', 'Testing & Validation', 'Product Design'],
        'apply_link': 'https://www.atherenergy.com/careers',
        },
        {
        'company_name': 'Ola Electric',
        'role': 'Automobile & E-Mobility Intern',
        'logo_initials': 'OE',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '3-6 Months',
        'description': 'Internship in electric vehicle product development, operations, supply chain and R&D; often listed on company career portals and LinkedIn. ',
        'skills': ['E-Mobility Design', 'Product Support', 'Supply Chain Basics', 'Vehicle Testing', 'Documentation'],
        'apply_link': 'https://olaelectric.com/careers',
        },
        {
        'company_name': 'Internshala (Automobile Engineering Internships)',
        'role': 'Automobile Engineering Intern',
        'logo_initials': 'IN',
        'location': 'Online/Offline (Various Cities including Bangalore)',
        'duration': '1-6 Months (varies by posting)',
        'description': 'Portal listing multiple automobile internships including design, vehicle maintenance, automotive engineering support and remote roles. ',
        'skills': ['AutoCAD', 'Vehicle Diagnostics', 'Quality Inspection', 'Documentation', 'Field Assistance'],
        'apply_link': 'https://internshala.com/internships/automobile-engineering-internship',
        },
        {
        'company_name': 'Fyn (EV & Automotive Startup)',
        'role': 'Automobile Engineering Intern',
        'logo_initials': 'FY',
        'location': 'Offline (Bangalore)',
        'duration': '1-6 Months (varies)',
        'description': 'Internship involving vehicle servicing, testing, prototyping, IoT device management, and coordination with partners — especially EV logistics and fleet systems. ',
        'skills': ['Vehicle Servicing', 'Prototyping', 'IoT Basics', 'Testing & Validation', '2W/4W Handling'],
        'apply_link': 'https://jobs.weekday.works/fyn-automobile-engineering-internship-in-bangalore',
        },
        {
        'company_name': 'Tata Motors',
        'role': 'Automobile Engineering Intern',
        'logo_initials': 'TM',
        'location': 'Online/Offline (India-wide opportunities including Bangalore)',
        'duration': '2-6 Months (typical)',
        'description': 'Internships covering automotive engineering, powertrain, vehicle design, and production systems — posted seasonally on Tata Motors career portal. ',
        'skills': ['Vehicle Dynamics', 'Powertrain Basics', 'Automotive Design', 'Testing & Quality', 'Team Work'],
        'apply_link': 'https://www.tatamotors.com/careers',
        },
        {
        'company_name': 'Mahindra & Mahindra',
        'role': 'Automobile Engineering Intern',
        'logo_initials': 'MM',
        'location': 'Online/Offline (India-wide)',
        'duration': '3-6 Months',
        'description': 'Internship in automotive engineering covering chassis, engines, R&D basics, and testing; posted via Mahindra careers portal or recruitment platforms. ',
        'skills': ['Chassis Design', 'Engine Testing', 'Quality Inspection', 'CAD Tools', 'Project Support'],
        'apply_link': 'https://www.mahindra.com/careers',
        },
        {
        'company_name': 'TVS Motor Company',
        'role': 'Automobile Engineering Intern',
        'logo_initials': 'TV',
        'location': 'Offline/Hybrid (Industrywide opportunities)',
        'duration': '1-3 Months',
        'description': 'Internship opportunities in vehicle design, engine systems, automotive electronics and manufacturing tracked via TVS Motor careers or internship listings. ',
        'skills': ['Engine Systems', 'Automotive Electronics', 'Manufacturing Basics', 'Maintenance Support', 'Documentation'],
        'apply_link': 'https://www.tvsmotor.com/careers',
        },
        {
        'company_name': 'Bosch India (Automotive Division)',
        'role': 'Automotive Engineering Intern',
        'logo_initials': 'BI',
        'location': 'Offline (Industry R&D & Test Sites)',
        'duration': '1-6 Months',
        'description': 'Internship in automotive systems, sensors, powertrain components and diagnostics — worth checking via Bosch India careers or LinkedIn for openings. ',
        'skills': ['Diagnostics', 'Automotive Sensors', 'Powertrain Components', 'Testing Tools', 'Report Writing'],
        'apply_link': 'https://www.bosch.in/careers',
        },
        {
        'company_name': 'Dynamatic Technologies',
        'role': 'Automotive/Precision Engineering Intern',
        'logo_initials': 'DT',
        'location': 'Offline (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Engineering internship with a precision engineering supplier to automotive and aerospace industries — great for learning manufacturing, components & systems. ',
        'skills': ['Precision Machining', 'Automotive Components', 'Manufacturing Support', 'Quality Control', 'Documentation'],
        'apply_link': 'https://dynamatics.com/careers',
        },

    ]
    ice_internshi = [
        {
        'company_name': 'Sanfoundry',
        'role': 'Systems & Control / Instrumentation Intern',
        'logo_initials': 'SF',
        'location': 'Online / Bangalore',
        'duration': '1-6 Months',
        'description': 'Internships focused on systems, control theory, signals, instrumentation basics, process control, and related engineering tutorial creation & problem solving. Good for theory + application exposure. ',
        'skills': ['Control Systems', 'Signal Analysis', 'Feedback Systems', 'Process Control', 'Instrumentation Basics'],
        'apply_link': 'https://www.sanfoundry.com/internships-instrumentation-engineering/',
        },
        {
        'company_name': 'Internshala (Instrumentation & Control Listings)',
        'role': 'Instrumentation & Control Engineering Intern',
        'logo_initials': 'IN',
        'location': 'Online / Offline (Bangalore & Other Cities)',
        'duration': '1-6 Months (varies by role)',
        'description': 'Platform aggregating multiple internships in instrumentation, control systems, embedded systems, automation, PCB design, test & measurement roles near Bangalore and across India. ',
        'skills': ['Embedded Systems', 'Sensors & Actuators', 'Control Systems', 'Automation', 'Circuit Design'],
        'apply_link': 'https://internshala.com/internships/instrumentation-and-control-engineering-internship-in-bangalore',
        },
        {
        'company_name': 'Innotech Automation Pvt. Ltd.',
        'role': 'Instrumentation & Automation Intern',
        'logo_initials': 'IA',
        'location': 'Offline / Bangalore area',
        'duration': '1-3 Months',
        'description': 'Company known for automation systems & sensor integration — suitable for practical PLC/SCADA and instrumentation exposure (recorded in student internship placements). ',
        'skills': ['PLC/SCADA Basics', 'Industrial Sensors', 'Automation', 'Control Systems', 'Field Measurements'],
        'apply_link': 'https://www.innotechautomation.com',  # company homepage (search careers)
        },
        {
        'company_name': 'Axis Solutions Pvt. Ltd.',
        'role': 'Instrumentation Intern',
        'logo_initials': 'AS',
        'location': 'Offline / Bangalore area',
        'duration': '1-3 Months',
        'description': 'Engineering firm engaged in instrumentation & control projects with hands-on learning for students across sensors, instrumentation design, and integration. ',
        'skills': ['Instrumentation Design', 'Measurement Techniques', 'Control Basics', 'Documentation', 'Team Projects'],
        'apply_link': 'https://www.axissolutions.in',  # company homepage
        },
        {
        'company_name': 'MASIBUS Pvt. Ltd.',
        'role': 'Instrumentation & Control Intern',
        'logo_initials': 'MB',
        'location': 'Offline / Bangalore area',
        'duration': '1-3 Months',
        'description': 'Instrumentation product company — exposure to industrial instrumentation devices, process measurement systems, and control elements (documented intern placements). ',
        'skills': ['Industrial Instrumentation', 'Sensors', 'Signal Conditioning', 'Control Fundamentals', 'Testing'],
        'apply_link': 'https://www.masibus.com/',
        },
        {
        'company_name': 'Soul Electric Pvt. Ltd.',
        'role': 'Control Systems / Instrumentation Intern',
        'logo_initials': 'SE',
        'location': 'Offline / Bangalore area',
        'duration': '2-4 Months',
        'description': 'Electrical & instrumentation firm where trainees work on control systems, measurement, and electrical instrumentation (interns have received stipends historically). ',
        'skills': ['Control Systems', 'PLC Basics', 'Electrical Instrumentation', 'Testing', 'Measurement Tools'],
        'apply_link': 'https://soulectric.com/',
        },
        {
        'company_name': 'PLC/SCADA Training Institutes (Bangalore)',
        'role': 'Industrial Instrumentation Intern',
        'logo_initials': 'PT',
        'location': 'Offline / Bangalore',
        'duration': '1-3 Months',
        'description': 'Training organizations in PLC/SCADA & DCS (which often provide internship + certificate programs with practical lab exposure). Good for foundational automation skills. ',
        'skills': ['PLC Programming', 'SCADA', 'DCS Basics', 'Instrumentation', 'Process Automation'],
        'apply_link': 'https://internshala.com/internships/instrumentation-and-control-engineering-internship-in-bangalore',
        },
        {
        'company_name': 'Embedded & IoT Platforms (via Internshala)',
        'role': 'Instrumentation & Embedded Intern',
        'logo_initials': 'EI',
        'location': 'Online / Hybrid',
        'duration': '1-4 Months',
        'description': 'Internships involving sensors, microcontrollers, data acquisition, and control loop fundamentals — good stepping stone into instrumentation and automation roles. ',
        'skills': ['Arduino/Raspberry Pi', 'Sensors & Interfacing', 'Control Logic', 'Data Acquisition', 'Python/C Programming'],
        'apply_link': 'https://internshala.com/internships/instrumentation-and-control-engineering-internship-in-bangalore',
        },
        {
        'company_name': 'Control & Automation Startups (via LinkedIn)',
        'role': 'Instrumentation/Automation Intern',
        'logo_initials': 'CA',
        'location': 'Offline/Hybrid (Bangalore)',
        'duration': '1-6 Months',
        'description': 'Startups working on automation, industrial control products, IoT systems, and process instrumentation advertise intern roles on LinkedIn & other portals. ',
        'skills': ['Industrial Automation', 'Control Systems', 'Sensor Networks', 'Documentation', 'Team Projects'],
        'apply_link': 'https://www.linkedin.com/jobs/instrumentation-intern-jobs-bengaluru',
        },
        {
        'company_name': 'Automation & Industrial Solutions Firms',
        'role': 'Instrumentation Intern',
        'logo_initials': 'AI',
        'location': 'Offline / Bangalore & nearby',
        'duration': '1-6 Months',
        'description': 'Local industrial automation service providers that hire interns for sensor calibration, control panel basics, and process measurement work — search on portals. ',
        'skills': ['Process Measurement', 'Calibration', 'Instrumentation Tools', 'Report Writing', 'Team Work'],
        'apply_link': 'https://internshala.com/internships/instrumentation-and-control-engineering-internship-in-bangalore',
        },

    ]
    
    # Select appropriate internships based on branch
    # Select appropriate internships based on branch
    if branch == 'mech':
        internships_data = mech_internships
    elif branch == 'civil':
        internships_data = civil_internships
    elif branch == 'eee':
        internships_data = eee_internship
    elif branch == 'ece':
        internships_data = ece_internship
    elif branch == 'auto':
        internships_data = auto_internship
    elif branch == 'ice':
        internships_data = auto_internship
    else:  # cse or ist
        internships_data = cse_ist_internships
    
    return render(request, 'internships.html', {
        'branch': branch,
        'branch_name': branch_name,
        'internships': internships_data
    })

def student_upload_verify_view(request, branch, semester):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        messages.error(request, 'Please login first.')
        return redirect('role_selection')
    
    # Branch names mapping
    branch_names = {
        'cse': 'Computer Science & Engineering',
        'civil': 'Civil Engineering',
        'auto': 'Automobile Engineering',
        'eee': 'Electrical & Electronics Engineering',
        'ece': 'Electronics & Communication Engineering',
        'ist': 'Information Science & Technology',
        'ice': 'Instrumentation & Control Engineering',
        'mech': 'Mechanical Engineering',
    }
    
    branch_name = branch_names.get(branch, 'Unknown Branch')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Student upload password
        STUDENT_UPLOAD_PASSWORD = 'student123'
        
        if password == STUDENT_UPLOAD_PASSWORD:
            request.session['student_upload_verified'] = True
            messages.success(request, 'Verification successful! You can now upload.')
            return redirect('student_upload_form', branch=branch, semester=semester)
        else:
            messages.error(request, 'Incorrect password!')
            return redirect('student_upload_verify', branch=branch, semester=semester)
    
    return render(request, 'student_upload.html', {
        'branch': branch,
        'semester': semester,
        'branch_name': branch_name
    })


def student_upload_form_view(request, branch, semester):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        messages.error(request, 'Please login first.')
        return redirect('role_selection')
    
    # Check if student verified with password
    if not request.session.get('student_upload_verified'):
        messages.error(request, 'Please verify with password first.')
        return redirect('student_upload_verify', branch=branch, semester=semester)
    
    # Branch names mapping
    branch_names = {
        'cse': 'Computer Science & Engineering',
        'civil': 'Civil Engineering',
        'auto': 'Automobile Engineering',
        'eee': 'Electrical & Electronics Engineering',
        'ece': 'Electronics & Communication Engineering',
        'ist': 'Information Science & Technology',
        'ice': 'Instrumentation & Control Engineering',
        'mech': 'Mechanical Engineering',
    }
    
    branch_name = branch_names.get(branch, 'Unknown Branch')
    
    if request.method == 'POST':
        doc_type = request.POST.get('doc_type')
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        year = request.POST.get('year')
        file = request.FILES.get('file')
        uploaded_by = request.session.get('user_email', 'student')
        
        # Get college from session
        college = request.session.get('college')
        
        # Create new question paper entry
        paper = QuestionPaper.objects.create(
            branch=branch,
            college=college,
            semester=semester,
            doc_type=doc_type,
            title=title,
            subject=subject,
            year=year,
            uploaded_by=uploaded_by,
            file=file
        )
        
        # Send notification to students
        send_upload_notification(
            college=college,
            branch=branch,
            semester=semester,
            doc_type=doc_type,
            title=title,
            subject=subject,
            uploaded_by=uploaded_by,
            file_path=paper.file.name
        )
        
        # Clear the verification
        request.session['student_upload_verified'] = False
        
        messages.success(request, 'Document uploaded successfully!')
        return redirect('view_notes', branch=branch, semester=semester)
    
    return render(request, 'student_upload_form.html', {
        'branch': branch,
        'semester': semester,
        'branch_name': branch_name
    })


def dashboard_view(request):
    # Check if user is authenticated
    if not request.session.get('authenticated'):
        return redirect('login')
    
    return render(request, 'dashboard.html')


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    return redirect('role_selection')