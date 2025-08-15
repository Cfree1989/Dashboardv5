# 3D Print Management System

A comprehensive Flask API + Next.js system for managing 3D print job workflows in academic/makerspace environments.

## Features

- **Student Submission**: Easy file upload and job submission interface
- **Staff Dashboard**: Complete job management with real-time updates
- **Workflow Management**: Complete job lifecycle from submission to pickup
- **File Integrity**: Robust file management with metadata tracking
- **Audit Trails**: Comprehensive event logging for all actions
- **Email Notifications**: Automated email confirmations and updates
- **Protocol Handler**: Direct file opening in slicer software
- **Multi-User Support**: Workstation-based authentication with staff attribution

## Quick Start

### Prerequisites

- Docker Desktop
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Dashboardv5
```

2. **Configure Environment Variables** (CRITICAL - Security Setup):
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and update the following CRITICAL values:
# - POSTGRES_PASSWORD: Generate a secure password
# - SECRET_KEY: Generate a secure secret key
# - STAFF_PASSWORD: Set a secure staff password
# - MAIL_USERNAME/MAIL_PASSWORD: Use real email credentials

# Generate secure credentials:
python -c "import secrets; print('Secure SECRET_KEY:', secrets.token_urlsafe(32))"
python -c "import secrets; print('Secure POSTGRES_PASSWORD:', secrets.token_urlsafe(16))"
python -c "import secrets; print('Secure STAFF_PASSWORD:', secrets.token_urlsafe(12))"
```

3. Start the development environment:
```bash
docker-compose up -d --build
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

### Security Notes

⚠️ **IMPORTANT**: This system contains sensitive configuration. Always:
- Use secure, randomly generated passwords
- Never commit `.env` files to version control
- Use different credentials for development, staging, and production
- Regularly rotate passwords and secret keys

## Project Structure

```
Dashboardv5/
├── backend/                 # Flask API
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── migrations/         # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js application
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   ├── components/    # React components
│   │   ├── lib/          # Utility libraries
│   │   └── types/        # TypeScript types
│   └── package.json      # Node.js dependencies
├── storage/               # File storage
│   ├── Uploaded/         # New submissions
│   ├── Pending/          # Awaiting confirmation
│   ├── ReadyToPrint/     # Ready for production
│   ├── Printing/         # Currently printing
│   ├── Completed/        # Awaiting pickup
│   ├── PaidPickedUp/     # Process complete
│   └── Archived/         # Long-term storage
├── docs/                 # Documentation
├── tests/                # Test files
└── scripts/              # Utility scripts
```

## Job Status Flow

1. **UPLOADED** → Student submitted, awaiting staff review
2. **PENDING** → Approved by staff, awaiting student confirmation
3. **READYTOPRINT** → Student confirmed, ready for printing
4. **PRINTING** → Currently being printed
5. **COMPLETED** → Print finished, awaiting pickup
6. **PAIDPICKEDUP** → Student paid and collected print
7. **REJECTED** → Staff rejected submission
8. **ARCHIVED** → Final state for old jobs

## Development

### Backend Development

The Flask API provides:
- RESTful endpoints for job management
- File upload and processing
- Email notifications
- Event logging
- Authentication and authorization

### Frontend Development

The Next.js application provides:
- Student submission interface
- Staff dashboard
- Real-time updates
- Modern UI/UX design

### Database

PostgreSQL database with the following main tables:
- `jobs` - Job information and status
- `events` - Audit trail for all actions
- `staff` - Staff member management
- `payments` - Payment tracking

## Configuration

Environment variables are configured in the `.env` file (copy from `.env.example`):

### Critical Security Variables
- `POSTGRES_PASSWORD` - Database password (generate secure random)
- `SECRET_KEY` - Flask secret key (generate secure random)
- `STAFF_PASSWORD` - Staff authentication password (generate secure random)
- `MAIL_USERNAME/MAIL_PASSWORD` - Email service credentials

### Application Configuration
- `DATABASE_URL` - PostgreSQL connection string (auto-generated)
- `REDIS_URL` - Redis connection string
- `FRONTEND_PUBLIC_URL` - Frontend URL for email links
- `STORAGE_PATH` - File storage directory
- `ALLOWED_MODEL_EXTS` - Allowed file extensions for uploads

### Development Settings
- `FLASK_ENV` - Flask environment (development/production)
- `FLASK_DEBUG` - Debug mode toggle
- `ANALYTICS_CACHE_TTL` - Analytics cache duration

See `.env.example` for complete documentation of all available variables.

## Contributing

1. Follow the established coding conventions
2. Write tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

This project is designed for academic/makerspace use.

## Support

For technical support or questions, please refer to the documentation in the `docs/` directory. 