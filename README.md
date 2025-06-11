# Course Management System (CMS) using Django

This project is a Course Management System (CMS) developed with Django, designed to streamline course management for instructors and assignment submission for students. The system supports file uploads, user authentication, and role-based access for instructors and students. 

The platform is hosted on AWS EC2, utilizing PostgreSQL RDS for database management, S3 for file storage, and GoDaddy for domain management. It is currently live at [www.aamusmartcms.com](http://www.aamusmartcms.com), in the User Acceptance Testing (UAT) phase, and will support over 500 students each semester. Data collected from the system is used to develop a machine learning reinforcement model.

## Key Features:
- **User Authentication:** Separate login systems for students and instructors
- **Instructor Dashboard:** Manage and upload courses, grade assignments, and manage student submissions
- **Student Dashboard:** Submit assignments and track progress
- **File Upload Support:** Upload and manage course materials and assignments
- **Assignment Grading:** Automatically or manually grade assignments

## Future Updates:
- **Notification System:** Alerts and reminders for students and instructors
- **Generative AI Integration:** Personalized learning experiences using AI models

## Technologies:
- **Backend:** Python, Django
- **Database:** PostgreSQL (RDS)
- **Hosting:** AWS EC2, GoDaddy for domain management
- **Storage:** AWS S3 for file storage
- **Frontend:** Bootstrap, HTML/CSS, JavaScript
- **Other Tools:** SQLite (for local development)

## Deployment:
The CMS is deployed at [www.aamusmartcms.com](http://www.aamusmartcms.com) and will be used by over 500 students each semester.

### Acknowledgment

This research is supported by the **National Science Foundation (NSF)** under **Award No. 2236002**, titled:  
**“Improving Programming Skills of Engineering Students at Historically Black Colleges and Universities Using AI-enhanced Personalized Adaptive Learning Tools.”**
