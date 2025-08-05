# 3D Print System - Installation Guide

## Overview

This guide will walk you through setting up the 3D Print Management System on a new computer. The system is a Flask-based web application with a PostgreSQL database, designed for academic/makerspace environments.

**⚠️ Important**: This guide includes detailed troubleshooting steps based on real-world installation experiences.

## Prerequisites

### Required Software

#### 1. Python 3.9 or Higher
**Download**: [Python.org](https://www.python.org/downloads/)
- **Windows**: Download the Windows installer. 
  **⚠️ CRITICAL (Windows Installation):**
    1. On the first screen of the Python installer, **YOU MUST CHECK THE BOX** at the bottom that says **"Add Python 3.x to PATH"** (or similar like "Add python.exe to PATH" / "Add Python to environment variables"). This is essential for Python to be accessible from the command line.
    2. After installation, **CLOSE ALL PowerShell/Command Prompt windows** and open a new one for the PATH changes to take effect.
- **macOS**: Use the macOS installer or install via Homebrew: `brew install python`
- **Linux**: Usually pre-installed, or install via package manager: `sudo apt install python3 python3-pip`

**Verify Installation**:
```bash
python --version
pip --version
```
**Troubleshooting (Windows):**
- If `python` or `pip` commands are not recognized after installation:
    1. You likely missed checking "Add Python to PATH" during installation.
    2. **Solution 1 (Recommended):** Uninstall Python completely from "Add or remove programs", then reinstall, making sure to check the "Add Python to PATH" box.
    3. **Solution 2 (Manual PATH edit - Advanced):**
        - Find your Python installation directory (e.g., `C:\Users\YourUserName\AppData\Local\Programs\Python\Python3X` or `C:\Program Files\Python3X`).
        - Add this directory AND its `Scripts` subdirectory (e.g., `C:\Users\YourUserName\AppData\Local\Programs\Python\Python3X\Scripts`) to your system's PATH environment variables.
        - Restart your terminal after making these changes.

#### 2. PostgreSQL Database
**Download**: [PostgreSQL.org](https://www.postgresql.org/downloads/)
- **Windows**: Use the Windows installer from EnterpriseDB
- **macOS**: Use the macOS installer or Homebrew: `brew install postgresql`
- **Linux**: Install via package manager: `sudo apt install postgresql postgresql-contrib`

**⚠️ CRITICAL**: During installation, set the postgres user password to `fablab` for consistency.

**Initial Setup**:
```bash
# Start PostgreSQL service (varies by OS)
# Windows: Starts automatically after installation
# macOS with Homebrew: brew services start postgresql
# Linux: sudo systemctl start postgresql
```

#### 3. Node.js and npm (for CSS compilation)
**Download**: [Node.js.org](https://nodejs.org/)
- Download and install the LTS (Long Term Support) version for your operating system.
- **Windows Installation Notes:**
    1. During installation, ensure that "Add to PATH" is selected (usually default).
    2. After installation, **CLOSE ALL PowerShell/Command Prompt windows** and open a new one.
    3. **PowerShell Execution Policy (If `npm` fails):** If `npm` commands give an error like "running scripts is disabled on this system" or "UnauthorizedAccess":
        - Open a new PowerShell window **as Administrator**.
        - Run the command: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
        - Press 'Y' and Enter if prompted to confirm.
        - Close the admin PowerShell and open a regular one. `npm --version` should now work.

**Verify Installation**:
```bash
node --version
npm --version
```
**Troubleshooting (Node.js/npm):**
- If `node` or `npm` are not found: Ensure Node.js was installed with "Add to PATH" selected and that you've restarted your terminal.
- If `npm install` or `npm run build-css` fails with errors about missing modules (e.g., `Cannot find module 'tailwindcss/lib/cli.js'`):
    1. Navigate to the `3DPrintSystem` sub-directory (where `package.json` is).
    2. Delete the `node_modules` directory: `Remove-Item node_modules -Recurse -Force` (in PowerShell).
    3. Re-run `npm install`.
    4. If issues persist with Tailwind, try explicitly: `npm install tailwindcss @tailwindcss/forms --save-dev`.

#### 4. Git (for version control)
**Download**: [Git-scm.com](https://git-scm.com/downloads/)
- Install Git for your operating system

**Verify Installation**:
```bash
git --version
```

### Optional but Recommended

#### 5. Visual Studio Code
**Download**: [code.visualstudio.com](https://code.visualstudio.com/)
- Excellent Python and web development support

#### 6. pgAdmin (PostgreSQL GUI)
**Download**: [pgAdmin.org](https://www.pgadmin.org/download/)
- Essential for database management and troubleshooting

## Installation Steps

### Step 1: Clone the Repository

```bash
# Navigate to your desired directory
cd /path/to/your/projects

# Clone the repository
git clone https://github.com/Cfree1989/3DPrintSystemV3.git

# Navigate to the project directory
cd 3DPrintSystemV3
```

### Step 2: Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
# Ensure you are in the project root (e.g., C:\3DPrintSystemV3)
# If venv\Scripts\activate gives an error:
# Try the PowerShell specific script:
.\venv\Scripts\Activate.ps1 
# If it still fails, the venv might not have created correctly.
# Try: python -m venv .\venv 
# Then attempt activation again.
# If venv continues to fail, for development, you can proceed without it
# but it's highly recommended for isolating dependencies.
# macOS/Linux:
source venv/bin/activate

# Verify virtual environment is active (should show (venv) in prompt)
```

### Step 3: Install Python Dependencies

```bash
# Install all required Python packages
pip install -r requirements.txt

# CRITICAL: Install PostgreSQL driver separately if needed
pip install psycopg2-binary

# Verify Flask installation
flask --version
```

### Step 4: Install Node.js Dependencies

```bash
# Navigate to the Flask app directory
cd 3DPrintSystem

# Install Node.js dependencies for Tailwind CSS
npm install

# Verify Tailwind installation
npx tailwindcss --help
```

**⚠️ If `npx tailwindcss --help` or `npm run build-css` fails with module not found:**
   This usually indicates an issue with the `node_modules` directory within `3DPrintSystemV3/3DPrintSystem/`.
   1. `cd 3DPrintSystem` (if not already there).
   2. `Remove-Item node_modules -Recurse -Force` (PowerShell command to delete the folder).
   3. `npm install` (to reinstall all Node.js dependencies cleanly).
   4. Then try `npm run build-css` or `npx tailwindcss --help` again.

### Step 5: Database Setup

#### 5A: Create Database and User in pgAdmin

1. **Open pgAdmin** and connect with:
   - Username: `postgres`
   - Password: `fablab` (the password you set during PostgreSQL installation)

2. **Create Database**:
   - Right-click "Databases" → Create → Database
   - Database name: `3d_print_system`
   - Owner: `postgres`

3. **Create User and Set Permissions**:
   - Open Query Tool (SQL icon)
   - Run this SQL:

```sql
-- Create user
CREATE USER fablab_user WITH PASSWORD 'fablab';

-- Grant basic privileges
GRANT ALL PRIVILEGES ON DATABASE "3d_print_system" TO fablab_user;

-- CRITICAL: Grant schema permissions (fixes common permission errors)
GRANT ALL PRIVILEGES ON SCHEMA public TO fablab_user;
GRANT CREATE ON SCHEMA public TO fablab_user;
GRANT USAGE ON SCHEMA public TO fablab_user;

-- Grant table and sequence permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fablab_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO fablab_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fablab_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO fablab_user;

-- Make fablab_user the owner (recommended)
ALTER DATABASE "3d_print_system" OWNER TO fablab_user;
```

### Step 6: Environment Configuration

Create a `.env` file in the project root directory (`3DPrintSystemV3/.env`):

```bash
# Navigate back to project root
cd ..

# Create .env file (use your preferred text editor)
# Windows:
notepad .env
# macOS/Linux:
nano .env
# Or use VS Code:
code .env
```

**Copy this EXACT .env file contents** 

Get .env from Project Owner.
```


### Step 7: Create Database Tables

#### Method 1: Using Flask Migrations (Preferred)

```bash
# Navigate to the Flask app directory
cd 3DPrintSystem

# Set environment variable for Flask app
# Windows:
set FLASK_APP=app.py
# macOS/Linux:
export FLASK_APP=app.py

# Try to create migration
flask db migrate -m "Initial migration"

# Apply migration to database
flask db upgrade
```

#### Method 2: Manual Table Creation (If migrations fail)

If you encounter permission errors, create tables manually in pgAdmin:

**In pgAdmin Query Tool for the `3d_print_system` database:**

```sql
-- Create the Job table
CREATE TABLE IF NOT EXISTS job (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'UPLOADED',
    student_name VARCHAR(100) NOT NULL,
    student_email VARCHAR(100) NOT NULL,
    student_discipline VARCHAR(100) NOT NULL,
    student_class_number VARCHAR(50),
    print_method VARCHAR(50) NOT NULL,
    color VARCHAR(50),
    material VARCHAR(50) NOT NULL,
    printer VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    weight_grams DECIMAL(10,2),
    print_time_hours DECIMAL(10,2),
    cost DECIMAL(10,2),
    staff_notes TEXT,
    staff_viewed_at TIMESTAMP,
    confirmation_token VARCHAR(255),
    token_expires_at TIMESTAMP
);

-- Create the Event table
CREATE TABLE IF NOT EXISTS event (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES job(id),
    event_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Create alembic version table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
```

**Verify Tables Created**:
- In pgAdmin, expand `3d_print_system` → `Schemas` → `public` → `Tables`
- You should see: `job`, `event`, and `alembic_version`

### Step 8: Build CSS Assets

```bash
# Still in 3DPrintSystem directory
# Build Tailwind CSS (development mode with watch)
npm run build-css

# Or for production (minified):
npm run build-css-prod
```

### Step 9: Create Storage Directories

The storage directories should be created automatically by the application, but you can create them manually if needed:

```bash
# In 3DPrintSystem directory
mkdir -p storage/Uploaded
mkdir -p storage/Pending  
mkdir -p storage/ReadyToPrint
mkdir -p storage/Printing
mkdir -p storage/Completed
mkdir -p storage/PaidPickedUp
mkdir -p storage/thumbnails
```

## Running the Application

### Development Mode

```bash
# Ensure you're in the 3DPrintSystem directory
cd 3DPrintSystem

# Ensure virtual environment is active
# (should see (venv) in command prompt)

# Run the Flask development server
python app.py
```

The application will be available at: `http://localhost:5000` or `http://127.0.0.1:5000`

**Expected Output**:
```
* Serving Flask app 'app'
* Debug mode: on
* Running on http://127.0.0.1:5000
Press CTRL+C to quit
* Restarting with stat
* Debugger is active!
* Debugger PIN: xxx-xxx-xxx
```

**Note**: You may see `python-dotenv could not parse statement starting at line 33` - this is a warning and can be ignored if your .env file is correct.

### Production Mode

For production deployment, use a WSGI server like Waitress (already included in requirements):

```bash
# Install waitress (already in requirements.txt)
pip install waitress

# Run with Waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

## Accessing the Application

### Student Interface
- **URL**: `http://localhost:5000`
- **Purpose**: Submit 3D print requests
- **No login required**

### Staff Dashboard
- **URL**: `http://localhost:5000/dashboard/login`
- **Username**: Not required (shared password system)
- **Password**: `Fabrication` (from STAFF_PASSWORD in your .env file)

## Testing the Installation

### Basic Functionality Test

1. **Start the application**: `python app.py`
2. **Open browser**: Navigate to `http://localhost:5000`
3. **Test student submission**: Fill out the form with test data
4. **Test staff login**: Go to `/dashboard/login` and use password `Fabrication`
5. **Check database**: Verify the job was created in pgAdmin

### Database Connection Test

```bash
# Test database connection
python -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    print('Database connection successful!')
    print(f'Tables: {db.engine.table_names()}')
"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. PostgreSQL Connection Error
**Error**: `psycopg2.OperationalError: could not connect to server`
**Solutions**: 
- Ensure PostgreSQL is running
- Verify postgres password is `fablab`
- Check DATABASE_URL in .env file matches database setup
- Verify database `3d_print_system` exists
- Confirm user `fablab_user` exists with password `fablab`

#### 2. Permission Denied for Schema Public
**Error**: `permission denied for schema public`
**Solution**: Run the comprehensive permissions SQL in pgAdmin:
```sql
GRANT ALL PRIVILEGES ON SCHEMA public TO fablab_user;
GRANT CREATE ON SCHEMA public TO fablab_user;
GRANT USAGE ON SCHEMA public TO fablab_user;
ALTER DATABASE "3d_print_system" OWNER TO fablab_user;
```

#### 3. Module Not Found Errors
**Error**: `ModuleNotFoundError: No module named 'psycopg2'`
**Solution**:
- Ensure virtual environment is activated
- Run `pip install psycopg2-binary`
- Re-run `pip install -r requirements.txt`

#### 4. python-dotenv Parse Error
**Error**: `python-dotenv could not parse statement starting at line X`
**Solution**:
- Check .env file for any command lines or malformed entries
- Remove any lines that aren't KEY=VALUE format
- Ensure no trailing commands like `python app.py`

#### 5. CSS Not Loading
**Error**: Styles not appearing correctly
**Solution**:
- Run `npm run build-css` to compile Tailwind CSS
- Check that static files are being served correctly
- Verify npm dependencies are installed

#### 6. File Upload Errors
**Error**: File upload failures
**Solution**:
- Check storage directory permissions
- Verify STORAGE_PATH in .env file
- Ensure directories exist (run Step 9 again)

#### 7. Tables Not Appearing in pgAdmin
**Solution**:
- Refresh the database in pgAdmin (right-click database → Refresh)
- Expand Tables section under the `3d_print_system` database
- If tables don't exist, use Method 2 (Manual Table Creation)

#### 8. Flask Migration Errors
**Error**: Migration commands fail
**Solutions**:
- Use Method 2 (Manual Table Creation) instead
- Verify database permissions are correctly set
- Check that alembic_version table exists

### Getting Help

If you encounter issues:

1. **Check the logs**: Look at the Flask console output for error messages
2. **Verify prerequisites**: Ensure all required software is installed and working
3. **Check permissions**: Ensure PostgreSQL user has proper permissions
4. **Environment variables**: Double-check your .env file matches the template exactly
5. **Database connectivity**: Test connection using pgAdmin first

## Development Workflow

### Making Changes

1. **Activate virtual environment**: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
2. **Start CSS watcher**: `npm run build-css` (in 3DPrintSystem directory)
3. **Run Flask app**: `python app.py` (in 3DPrintSystem directory)
4. **Make changes**: Edit Python, HTML, or CSS files
5. **Test changes**: Refresh browser to see updates

### Database Changes

When modifying models:
```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

If migrations fail, update tables manually in pgAdmin.

### Adding New Dependencies

**Python packages**:
```bash
pip install package_name
pip freeze > requirements.txt
```

**Node.js packages**:
```bash
npm install package_name
```

## Next Steps

After successful installation:

1. **Test all functionality**: Submit a test job and process it through the workflow
2. **Configure email settings**: Update MAIL_* variables for your institution
3. **Set up file sharing**: Configure network storage if using multiple computers
4. **Configure backup procedures**: Set up regular database and file backups
5. **Review security settings**: Change default passwords for production use
6. **Set up monitoring**: Configure logging and error tracking

## Production Deployment Considerations

For production use:
- Change SECRET_KEY to a unique, secure value
- Update STAFF_PASSWORD to a strong password
- Use environment-specific email configuration
- Set up SSL/TLS certificates
- Configure proper database backups
- Set up log rotation
- Implement monitoring and alerting
- Configure firewalls and security groups
- Use a reverse proxy (nginx/Apache)

## Installation Verification Checklist

- [ ] PostgreSQL installed and running
- [ ] Database `3d_print_system` created
- [ ] User `fablab_user` created with proper permissions
- [ ] Python virtual environment active
- [ ] All Python dependencies installed
- [ ] Node.js dependencies installed
- [ ] .env file created with correct contents
- [ ] Database tables created (job, event, alembic_version)
- [ ] CSS compiled successfully
- [ ] Storage directories exist
- [ ] Flask app starts without errors
- [ ] Student form accessible at localhost:5000
- [ ] Staff dashboard accessible with password "Fabrication"
- [ ] Test job submission works
- [ ] pgAdmin shows tables and data

This installation guide incorporates real-world troubleshooting steps and should provide a smooth setup experience for new computers. 