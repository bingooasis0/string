Project "String"
Project "String" is a web-based network monitoring and analysis platform designed to provide real-time insights into network traffic. It aims to deliver the power of tools like Wireshark and Splunk in a modern, accessible web interface. The system ingests, stores, and visualizes data from various network protocols, starting with Syslog and Netflow.

Table of Contents
Project Goal

Current Status

Architecture

Technology Stack

Setup & Installation

Running the Application

Known Issues & Next Steps

Project Goal
The primary objective is to create a comprehensive, "plug-and-play" network monitoring solution. A user should be able to deploy a collector on an endpoint or configure a network device to send data to the String server and immediately begin seeing real-time analytics.

The current development phase focuses on building a robust prototype that proves the core data pipeline:

Ingestion: Reliably receive Syslog and Netflow (v9/IPFIX) data streams.

Persistence: Store all incoming data in a database for historical analysis.

Real-time Visualization: Display data live on the web UI as it arrives.

Current Status
The project has a solid foundational architecture with several key components fully operational.

✅ Syslog Collector: Fully Functional. The collector successfully receives, parses, stores in the database, and streams live syslog data to the UI.

✅ Database Persistence: Functional. The backend SQLite database is operational and correctly stores all received Syslog entries. The Django Admin panel is configured for direct data verification.

✅ Real-time Infrastructure: Functional. The backend (Django Channels, Redis) and frontend (WebSockets) are correctly configured and provide a stable real-time data pipeline.

✅ Frontend UI: Functional. A multi-page React application provides separate views for data types, a theme switcher, and a debug modal. It successfully fetches historical data on page load and displays live data.

❌ Netflow Collector: CRITICAL FAILURE. The Netflow collector script (start_netflow.py) is non-functional. Despite multiple attempts with different libraries and custom parsers, it currently fails to correctly parse data from the target Ubiquiti router. This is the project's primary blocker.

Architecture
The application uses a decoupled client-server architecture.

Backend (Django): A monolithic backend that handles all data processing, storage, and real-time communication.

Collectors: Standalone management commands (start_syslog.py, start_netflow.py) that run as persistent UDP servers.

API: A standard REST API built with Django to serve historical data from the database and handle service control requests.

WebSockets: Django Channels provides the real-time communication layer, using Redis as a message broker to push live data to the frontend.

Frontend (React): A single-page application (SPA) built with Vite that runs entirely in the browser.

It fetches initial data via the REST API.

It maintains persistent WebSocket connections to receive live data streams.

Technology Stack
Component

Technology

Backend

Python, Django

Real-time

Django Channels, WebSockets

Message Broker

Redis

Database

SQLite (for development)

Frontend

JavaScript, React, Vite

Styling

Plain CSS

Dependencies

asgiref, python-dotenv, scapy

Setup & Installation
These instructions are for setting up the development environment on a Windows machine.

Prerequisites
Git: Install Git for Windows.

Python: Install Python (ensure it's added to your PATH).

Node.js: Install Node.js LTS.

Redis: Download and install Redis for Windows.

1. Backend Setup
# Navigate to the backend directory
cd backend

# Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install required Python packages
pip install Django daphne channels channels-redis scapy python-dotenv

# Create the database tables
python manage.py makemigrations
python manage.py migrate

# Create an admin user to view the database
python manage.py createsuperuser

2. Frontend Setup
# Navigate to the frontend directory
cd frontend

# Install required JavaScript packages
npm install

3. Environment Configuration
You must create two .env files. These contain configuration and secrets and should never be committed to Git.

Backend: Create a file at backend/.env

SECRET_KEY='a-strong-random-secret-key'
DEBUG=True
SYSLOG_HOST=0.0.0.0
SYSLOG_PORT=514
NETFLOW_HOST=0.0.0.0
NETFLOW_PORT=2055

Frontend: Create a file at frontend/.env.development

VITE_SYSLOG_WEBSOCKET_URL=ws://127.0.0.1:8000/ws/syslog/
VITE_NETFLOW_WEBSOCKET_URL=ws://127.0.0.1:8000/ws/netflow/
VITE_STATUS_WEBSOCKET_URL=ws://127.0.0.1:8000/ws/status/

Running the Application
You need to run three services in three separate terminals. The collectors must be run with Administrator privileges.

1. Backend Server (Normal Terminal)

cd backend
.\venv\Scripts\activate
python manage.py runserver

2. Syslog Collector (Administrator Terminal)

# Open a new terminal AS ADMINISTRATOR
cd backend
.\venv\Scripts\activate
python manage.py start_syslog

3. Frontend Dev Server (Normal Terminal)

cd frontend
npm install
npm run dev

You can now access the application at the URL provided by the Vite server (usually http://localhost:5173).

Known Issues & Next Steps
CRITICAL: Fix the Netflow Collector: This is the highest priority. The start_netflow.py script needs to be completely rewritten. The current approach using Scapy has failed. The next attempt should be a simple, robust parser built from scratch using the raw hex data captured by the diagnostic tool.

Implement Real Service Controls: The "Start/Kill Service" buttons in the UI are currently simulated. The backend API exists but needs to be made more robust to handle process management reliably.

Enhance UI: Implement filtering, sorting, and searching in the data tables.

Develop Dashboard: Build out the Home page into a true dashboard with summary statistics and visualizations.
