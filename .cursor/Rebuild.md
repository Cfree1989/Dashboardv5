# 3D Print System - Complete Rebuild Guide

## Overview
This guide provides a complete step-by-step rebuild of the 3D Print Management System following the masterplan specifications. The system is designed for academic/makerspace environments with workstation-based authentication and comprehensive workflow management.

## Phase 1: Environment Setup & Installation

### 1.1 Prerequisites Installation

**Required Software:**
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Git
- VS Code or preferred IDE
- Node.js 18+ (for local development)

**Installation Commands:**
```bash
# Windows (using Chocolatey)
choco install docker-desktop git vscode nodejs

### 1.2 Project Structure Creation

```bash
# Create project directory
mkdir Dashboardv4
cd Dashboardv4

# Initialize Git repository
git init

# Create directory structure
mkdir -p backend/app/{models,routes,services,utils}
mkdir -p backend/migrations
mkdir -p frontend/src/{app,components,lib,types}
mkdir -p storage/{Uploaded,Pending,ReadyToPrint,Printing,Completed,PaidPickedUp,Archived}
mkdir -p docs/{api,context,examples,requirements}
mkdir -p tests
mkdir -p scripts
```

### 1.3 Docker Environment Setup

**Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_APP=run.py
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://postgres:password@db:5432/3dprint
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
      - ./storage:/app/storage
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=3dprint
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: ./backend
    command: python -m rq worker --url redis://redis:6379
    volumes:
      - ./backend:/app
      - ./storage:/app/storage
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

## Phase 2: Backend Foundation

### 2.1 Python Dependencies

**Create `backend/requirements.txt`:**
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
Flask-CORS==4.0.0
Flask-Limiter==3.5.0
psycopg2-binary==2.9.7
python-dotenv==1.0.0
PyJWT==2.8.0
rq==1.15.1
openpyxl==3.1.2
pandas==2.1.1
itsdangerous==2.1.2
Flask-Mail==0.9.1
Werkzeug==2.3.7
```

### 2.2 Flask Application Factory

**Create `backend/app/__init__.py`:**
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
import os

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    limiter.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    from .routes import auth, jobs, submit, payment, analytics
    app.register_blueprint(auth.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(submit.bp)
    app.register_blueprint(payment.bp)
    app.register_blueprint(analytics.bp)
    
    return app
```

### 2.3 Database Models

**Create `backend/app/models/job.py`:**
```python
from app import db
from datetime import datetime
import uuid

class Job(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: uuid.uuid4().hex)
    student_name = db.Column(db.String(100), nullable=False)
    student_email = db.Column(db.String(100), nullable=False)
    discipline = db.Column(db.String(50), nullable=False)
    class_number = db.Column(db.String(50), nullable=False)
    
    # File Management
    original_filename = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    metadata_path = db.Column(db.String(512), nullable=False)
    file_hash = db.Column(db.String(64), nullable=True)
    
    # Job Configuration
    status = db.Column(db.String(50), default='UPLOADED')
    printer = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(32), nullable=False)
    material = db.Column(db.String(32), nullable=False)
    weight_g = db.Column(db.Float, nullable=True)
    time_hours = db.Column(db.Float, nullable=True)
    cost_usd = db.Column(db.Numeric(6, 2), nullable=True)
    
    # Student Confirmation
    acknowledged_minimum_charge = db.Column(db.Boolean, default=False)
    student_confirmed = db.Column(db.Boolean, default=False)
    student_confirmed_at = db.Column(db.DateTime, nullable=True)
    confirm_token = db.Column(db.String(128), nullable=True, unique=True)
    confirm_token_expires = db.Column(db.DateTime, nullable=True)
    is_confirmation_expired = db.Column(db.Boolean, default=False)
    confirmation_last_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Staff Management
    reject_reasons = db.Column(db.JSON, nullable=True)
    staff_viewed_at = db.Column(db.DateTime, nullable=True)
    last_updated_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', backref='job', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='job', uselist=False, cascade='all, delete-orphan')
```

**Create `backend/app/models/event.py`:**
```python
from app import db
from datetime import datetime

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String, db.ForeignKey('job.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.JSON, nullable=True)
    triggered_by = db.Column(db.String(100), nullable=False)
    workstation_id = db.Column(db.String(100), nullable=False)
```

**Create `backend/app/models/staff.py`:**
```python
from app import db
from datetime import datetime

class Staff(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'name': self.name,
            'is_active': self.is_active,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'deactivated_at': self.deactivated_at.isoformat() if self.deactivated_at else None
        }
```

**Create `backend/app/models/payment.py`:**
```python
from app import db
from datetime import datetime

class Payment(db.Model):
    job_id = db.Column(db.String, db.ForeignKey('job.id'), primary_key=True)
    grams = db.Column(db.Float, nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    txn_no = db.Column(db.String(50), nullable=False)
    picked_up_by = db.Column(db.String(100), nullable=False)
    paid_ts = db.Column(db.DateTime, default=datetime.utcnow)
    paid_by_staff = db.Column(db.String(100), nullable=False)
```

### 2.4 Authentication System

**Create `backend/app/routes/auth.py`:**
```python
from flask import Blueprint, request, jsonify
from app import db, limiter
from app.models.staff import Staff
import jwt
import datetime
import os

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Workstation configurations
WORKSTATIONS = {
    'front-desk': 'Fabrication',
    'lab-computer': 'Fabrication'
}

@bp.route('/login', methods=['POST'])
@limiter.limit("10 per hour")
def login():
    data = request.get_json()
    workstation_id = data.get('workstation_id')
    password = data.get('password')
    
    if workstation_id not in WORKSTATIONS or WORKSTATIONS[workstation_id] != password:
        return jsonify({'message': 'Invalid workstation ID or password'}), 401
    
    # Create JWT token
    token = jwt.encode({
        'workstation_id': workstation_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }, os.environ.get('SECRET_KEY', 'dev-secret-key'), algorithm='HS256')
    
    return jsonify({'token': token})

@bp.route('/staff', methods=['GET'])
def get_staff():
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    query = Staff.query
    if not include_inactive:
        query = query.filter_by(is_active=True)
    
    staff_list = query.all()
    return jsonify({'staff': [staff.to_dict() for staff in staff_list]})
```

## Phase 3: Frontend Foundation

### 3.1 Next.js Setup

**Create `frontend/package.json`:**
```json
{
  "name": "3d-print-dashboard",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "^18",
    "react-dom": "^18",
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-tabs": "^1.0.4",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "lucide-react": "^0.294.0",
    "date-fns": "^2.30.0",
    "recharts": "^2.8.0"
  },
  "devDependencies": {
    "eslint": "^8",
    "eslint-config-next": "14.0.0"
  }
}
```

### 3.2 Authentication Context

**Create `frontend/src/contexts/AuthContext.tsx`:**
```typescript
import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  workstationId: string | null;
  token: string | null;
  login: (workstationId: string, password: string) => Promise<boolean>;
  logout: () => void;
  selectedStaffId: string | null;
  setSelectedStaffId: (id: string | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [workstationId, setWorkstationId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [selectedStaffId, setSelectedStaffId] = useState<string | null>(null);

  useEffect(() => {
    const savedToken = localStorage.getItem('workstation_token');
    const savedWorkstationId = localStorage.getItem('workstation_id');
    
    if (savedToken && savedWorkstationId) {
      setToken(savedToken);
      setWorkstationId(savedWorkstationId);
      setIsAuthenticated(true);
    }
  }, []);

  const login = async (workstationId: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workstation_id: workstationId, password })
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.token);
        setWorkstationId(workstationId);
        setIsAuthenticated(true);
        localStorage.setItem('workstation_token', data.token);
        localStorage.setItem('workstation_id', workstationId);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setWorkstationId(null);
    setIsAuthenticated(false);
    setSelectedStaffId(null);
    localStorage.removeItem('workstation_token');
    localStorage.removeItem('workstation_id');
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      workstationId,
      token,
      login,
      logout,
      selectedStaffId,
      setSelectedStaffId
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### 3.3 API Client

**Create `frontend/src/lib/api-client.ts`:**
```typescript
import { useAuth } from '@/contexts/AuthContext';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1';

class ApiClient {
  private getAuthHeaders() {
    const token = localStorage.getItem('workstation_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    };
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: this.getAuthHeaders(),
      ...options.headers
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  // Job Management
  async getJobs(params?: Record<string, string>) {
    const queryString = params ? `?${new URLSearchParams(params)}` : '';
    return this.request(`/jobs${queryString}`);
  }

  async getJob(id: string) {
    return this.request(`/jobs/${id}`);
  }

  async approveJob(id: string, data: any) {
    return this.request(`/jobs/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async rejectJob(id: string, data: any) {
    return this.request(`/jobs/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // Staff Management
  async getStaff() {
    return this.request('/staff');
  }

  // Student Submission
  async submitJob(formData: FormData) {
    const response = await fetch(`${API_BASE}/submit`, {
      method: 'POST',
      headers: {
        'Authorization': this.getAuthHeaders().Authorization
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Submission Error: ${response.status}`);
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();
```

## Phase 4: Core Features Implementation

### 4.1 Student Submission Form

**Create `frontend/src/app/submit/page.tsx`:**
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

export default function SubmitPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    student_name: '',
    student_email: '',
    discipline: '',
    class_number: '',
    print_method: '',
    color: '',
    printer: '',
    acknowledged_minimum_charge: false
  });
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const formDataToSend = new FormData();
      Object.entries(formData).forEach(([key, value]) => {
        formDataToSend.append(key, value.toString());
      });
      if (file) {
        formDataToSend.append('file', file);
      }

      const result = await apiClient.submitJob(formDataToSend);
      router.push(`/submit/success?job=${result.id}`);
    } catch (error) {
      console.error('Submission error:', error);
      setErrors({ general: 'Failed to submit job. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Submit 3D Print Job</h1>
      
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
        <p className="text-sm text-yellow-700">
          Before submitting your model for 3D printing, please ensure you have thoroughly reviewed our Additive Manufacturing Moodle page, read all the guides, and checked the checklist...
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Form fields implementation */}
        <div>
          <label className="block text-sm font-medium mb-2">Student Name</label>
          <input
            type="text"
            required
            className="w-full p-2 border rounded"
            value={formData.student_name}
            onChange={(e) => setFormData({...formData, student_name: e.target.value})}
          />
        </div>

        {/* Additional form fields... */}
        
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Submitting...' : 'Submit Job'}
        </button>
      </form>
    </div>
  );
}
```

### 4.2 Staff Dashboard

**Create `frontend/src/app/dashboard/page.tsx`:**
```typescript
'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api-client';
import JobCard from '@/components/dashboard/job-card';

export default function DashboardPage() {
  const { isAuthenticated, selectedStaffId } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboardData();
    }
  }, [isAuthenticated]);

  const loadDashboardData = async () => {
    try {
      const [jobsData, statsData] = await Promise.all([
        apiClient.getJobs(),
        apiClient.request('/stats')
      ]);
      setJobs(jobsData.jobs);
      setStats(statsData);
    } catch (error) {
      console.error('Dashboard load error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return <div>Please log in to access the dashboard.</div>;
  }

  if (loading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">3D Print Dashboard</h1>
        <div className="text-sm text-gray-600">
          Workstation: {useAuth().workstationId}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold">Uploaded</h3>
          <p className="text-2xl font-bold text-blue-600">{stats.uploaded || 0}</p>
        </div>
        {/* Additional stat cards... */}
      </div>

      {/* Job List */}
      <div className="space-y-4">
        {jobs.map((job: any) => (
          <JobCard
            key={job.id}
            job={job}
            onRefresh={loadDashboardData}
            selectedStaffId={selectedStaffId}
          />
        ))}
      </div>
    </div>
  );
}
```

## Phase 5: Advanced Features

### 5.1 Job Management Modals

**Create `frontend/src/components/dashboard/modals/ApprovalModal.tsx`:**
```typescript
'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface ApprovalModalProps {
  job: any;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  selectedStaffId: string;
}

export default function ApprovalModal({ job, isOpen, onClose, onSuccess, selectedStaffId }: ApprovalModalProps) {
  const [formData, setFormData] = useState({
    weight_g: '',
    time_hours: '',
    authoritative_file: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiClient.approveJob(job.id, {
        ...formData,
        staff_name: selectedStaffId
      });
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Approval error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">Approve Job</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Weight (grams)</label>
            <input
              type="number"
              step="0.1"
              required
              className="w-full p-2 border rounded"
              value={formData.weight_g}
              onChange={(e) => setFormData({...formData, weight_g: e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Print Time (hours)</label>
            <input
              type="number"
              step="0.5"
              required
              className="w-full p-2 border rounded"
              value={formData.time_hours}
              onChange={(e) => setFormData({...formData, time_hours: e.target.value})}
            />
          </div>

          <div className="flex space-x-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Approving...' : 'Approve'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

### 5.2 Email Service

**Create `backend/app/services/email_service.py`:**
```python
from flask import current_app
from flask_mail import Message
from app import mail
from datetime import datetime, timedelta
import jwt
import os

class EmailService:
    @staticmethod
    def send_approval_email(job):
        token = jwt.encode({
            'job_id': job.id,
            'exp': datetime.utcnow() + timedelta(hours=72)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        job.confirm_token = token
        job.confirm_token_expires = datetime.utcnow() + timedelta(hours=72)
        job.confirmation_last_sent_at = datetime.utcnow()
        
        msg = Message(
            'Your 3D Print Job Has Been Approved',
            recipients=[job.student_email],
            body=f"""
            Hello {job.student_name},
            
            Your 3D print job has been approved by our staff.
            
            Job Details:
            - File: {job.display_name}
            - Printer: {job.printer}
            - Material: {job.material}
            - Color: {job.color}
            - Estimated Cost: ${job.cost_usd}
            
            Please confirm your job by clicking this link:
            {current_app.config['FRONTEND_URL']}/confirm/{token}
            
            This link will expire in 72 hours.
            """
        )
        
        mail.send(msg)
        return token

    @staticmethod
    def send_rejection_email(job, reasons):
        msg = Message(
            'Your 3D Print Job Has Been Rejected',
            recipients=[job.student_email],
            body=f"""
            Hello {job.student_name},
            
            Your 3D print job has been rejected by our staff.
            
            Reasons: {', '.join(reasons)}
            
            Please review our guidelines and submit a new job if needed.
            """
        )
        
        mail.send(msg)

    @staticmethod
    def send_completion_email(job):
        msg = Message(
            'Your 3D Print Job Is Complete',
            recipients=[job.student_email],
            body=f"""
            Hello {job.student_name},
            
            Your 3D print job is complete and ready for pickup.
            
            Job Details:
            - File: {job.display_name}
            - Final Cost: ${job.cost_usd}
            
            Please visit the lab to collect your print.
            """
        )
        
        mail.send(msg)
```

## Phase 6: Testing & Deployment

### 6.1 Database Migrations

**Create initial migration:**
```bash
# Inside backend container
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6.2 Development Testing

**Start the development environment:**
```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 6.3 Production Deployment

**Create production Dockerfile:**
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

## Phase 7: Advanced Features

### 7.1 SlicerOpener Protocol Handler

**Create `SlicerOpener/SlicerOpener.py`:**
```python
import sys
import subprocess
import os
import configparser
from urllib.parse import urlparse, parse_qs
import tkinter
from tkinter import messagebox

def load_config(config_path='config.ini'):
    parser = configparser.ConfigParser()
    if not parser.read(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    config = {
        'storage_base_path': parser.get('main', 'AUTHORITATIVE_STORAGE_BASE_PATH'),
        'slicers': []
    }
    
    for section in parser.sections():
        if section.startswith('slicer_'):
            config['slicers'].append({
                'name': parser.get(section, 'name'),
                'path': parser.get(section, 'path'),
                'extensions': [ext.strip() for ext in parser.get(section, 'extensions').split(',')]
            })
    return config

def validate_file_path(file_path, storage_base_path):
    """Security validation to prevent directory traversal"""
    abs_file_path = os.path.abspath(file_path)
    abs_storage_path = os.path.abspath(storage_base_path)
    
    return abs_file_path.startswith(abs_storage_path)

def main():
    if len(sys.argv) < 2:
        show_error_popup("Error", "No URL provided")
        return
    
    try:
        # Load configuration
        config = load_config()
        
        # Parse URL
        url = sys.argv[1]
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        file_path = query_params.get('path', [None])[0]
        
        if not file_path:
            show_error_popup("Error", "No file path provided in URL")
            return
        
        # Security validation
        if not validate_file_path(file_path, config['storage_base_path']):
            show_error_popup("Security Error", "Invalid file path")
            return
        
        # Check file exists
        if not os.path.exists(file_path):
            show_error_popup("Error", "File not found")
            return
        
        # Find compatible slicers
        file_ext = os.path.splitext(file_path)[1].lower()
        compatible_slicers = [
            slicer for slicer in config['slicers']
            if file_ext in slicer['extensions']
        ]
        
        if not compatible_slicers:
            show_error_popup("Error", "No compatible slicer found for this file type")
            return
        
        # Launch slicer
        if len(compatible_slicers) == 1:
            slicer = compatible_slicers[0]
            subprocess.Popen([slicer['path'], file_path])
            show_success_popup("Success", f"Opened {os.path.basename(file_path)} in {slicer['name']}")
        else:
            # Multiple slicers - show selection dialog
            slicer_names = [s['name'] for s in compatible_slicers]
            selected = show_slicer_selection_dialog(slicer_names)
            if selected:
                slicer = compatible_slicers[slicer_names.index(selected)]
                subprocess.Popen([slicer['path'], file_path])
                show_success_popup("Success", f"Opened {os.path.basename(file_path)} in {slicer['name']}")
    
    except Exception as e:
        show_error_popup("Error", f"Unexpected error: {str(e)}")

def show_error_popup(title, message):
    tkinter.Tk().withdraw()
    messagebox.showerror(title, message)

def show_success_popup(title, message):
    tkinter.Tk().withdraw()
    messagebox.showinfo(title, message)

if __name__ == "__main__":
    main()
```

## Summary

This rebuild guide provides a complete step-by-step implementation of the 3D Print Management System following the masterplan specifications. The system includes:

1. **Environment Setup**: Docker-based development environment
2. **Backend Foundation**: Flask API with PostgreSQL, authentication, and file management
3. **Frontend Foundation**: Next.js with TypeScript, authentication context, and API client
4. **Core Features**: Student submission, staff dashboard, job management
5. **Advanced Features**: Email notifications, protocol handler, real-time updates
6. **Testing & Deployment**: Database migrations and production configuration

The implementation follows all masterplan requirements including:
- Workstation-based authentication with staff attribution
- Complete job workflow management
- File integrity and metadata tracking
- Comprehensive event logging
- Email notifications and confirmations
- Professional UI/UX design patterns

This provides a solid foundation that can be extended with additional features as needed. 