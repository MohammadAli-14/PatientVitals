# Patient Vitals Management System

A modern, professional web application for healthcare professionals to record, manage, and generate PDF reports of patient vital signs. Built with FastAPI, MongoDB, and modern web technologies.

## 🚀 Live Demo

[![Render Deployment](https://patientvitals.onrender.com)  

## ✨ Features

### 🏥 Core Functionality
- **Patient Vitals Recording**: Secure entry of comprehensive patient vital signs
- **Real-time Data Storage**: MongoDB-powered persistent data storage
- **Professional PDF Reports**: Automated generation of medical-grade PDF reports
- **RESTful API**: Fully documented API endpoints for integration

### 💻 Technical Features
- **Modern FastAPI Backend**: High-performance Python web framework with automatic API documentation
- **Async Database Operations**: Non-blocking MongoDB operations using Motor
- **Responsive UI**: Mobile-friendly interface that works on all devices
- **Real-time Validation**: Input validation with user-friendly error messages

### 📊 Vital Signs Tracked
- Heart Rate (BPM)
- Blood Pressure (Systolic/Diastolic)
- Respiratory Rate
- Body Temperature (°C)
- Oxygen Saturation (%)
- Clinical Notes

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server for production
- **Motor** - Async MongoDB driver
- **ReportLab** - PDF generation engine
- **Jinja2** - HTML templating engine
- **Python-dotenv** - Environment management

### Frontend
- **Vanilla JavaScript** - Modern ES6+ features
- **CSS3** - Custom properties, Grid, Flexbox
- **HTML5** - Semantic markup

### Database & Deployment
- **MongoDB** - NoSQL database
- **Render** - Cloud deployment platform
- **GitHub** - Version control

## 📁 Project Structure
fastapi-patient-vitals/
├── main.py # FastAPI application entry point
├── requirements.txt # Python dependencies
├── .env # Environment variables (local)
├── .gitignore # Git ignore rules
├── templates/
│ └── index.html # Main web interface
├── static/
│ ├── styles.css # Professional styling
│ └── script.js # Frontend functionality
└── reports/ # Generated PDF storage

text

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB database (local or MongoDB Atlas)
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/MohammadAli-14/PatientVitals.git
   cd PatientVitals
Create virtual environment

bash
python -m venv venv
On Windows: venv\Scripts\activate
On Mac/Linux: source venv/bin/activate
Install dependencies

bash
pip install -r requirements.txt
Environment setup
Create a .env file:

env
MONGO_URI=mongodb://localhost:27017/vitals_db
OR for MongoDB Atlas:
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/vitals_db
Run the application

bash
uvicorn main:app --reload
Access the application

Web Interface: http://localhost:8000

API Documentation: http://localhost:8000/docs

Alternative Docs: http://localhost:8000/redoc
