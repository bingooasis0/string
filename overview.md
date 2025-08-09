Project 'String' - Status Report & Technical Briefing
Date: August 9, 2025

1. Project Overview
1.1. Core Idea
Project 'String' is a web-based network monitoring and analysis tool. The vision is to create a powerful, user-friendly platform analogous to desktop applications like Wireshark or commercial cloud services like CloudShark. The system is designed to ingest, store, analyze, and display network data from various sources in real-time.

1.2. Primary Goal (Current Phase)
The immediate goal is to build a robust, working prototype that proves the core functionality of the platform. This includes:

Data Ingestion: Successfully receiving Syslog and Netflow (v9/IPFIX) data from network devices.

Data Persistence: Storing all incoming data in a structured database for historical analysis.

Real-time Visualization: Displaying the incoming data on a web interface live as it arrives.

Multi-Page UI: Creating a clean, multi-page user interface to separate different data types (Syslog, Netflow) and provide a central hub.

1.3. Current Progress
The project has made significant progress and has a solid foundational architecture.

Syslog Collector: The Syslog collector is fully functional. It successfully receives data from network devices, parses multiple formats, saves every entry to the database, and streams live updates to the frontend.

Database: The backend database is operational. It correctly stores all Syslog and Netflow records. The Django admin panel is configured for direct data access and verification.

Frontend UI: A multi-page React application has been built with separate views for a home/dashboard page, a Syslog viewer, and a Netflow viewer. It includes features like light/dark mode and a debug modal.

Real-time Infrastructure: The real-time pipeline is working. The backend uses Django Channels with a Redis message broker to push live updates to the frontend via WebSockets.

2. Architecture
The application is built on a modern, decoupled architecture:

Backend (Django): A powerful Python framework responsible for all data processing.

Collectors: Standalone Python scripts that run as services to listen for network traffic (Syslog, Netflow).

API Server: Handles requests from the frontend, such as fetching historical data from the database or starting/stopping collector services.

Real-time Server: Uses Django Channels and WebSockets to push live data to the frontend.

Database: A SQLite database managed by Django for data persistence.

Frontend (React): A JavaScript library responsible for the user interface.

It runs entirely in the user's browser.

It fetches historical data from the backend's API when a page loads.

It maintains a persistent WebSocket connection to the backend to receive live updates.

3. File Breakdown
3.1. Backend (/backend)
/manage.py: Django's primary command-line tool. Used to run the server, apply database changes (migrate), and run our custom collector scripts (start_syslog).

/.env: An environment configuration file. Crucially, this file is not committed to source control. It holds sensitive information like the SECRET_KEY and configuration variables for the collectors (e.g., SYSLOG_PORT).

/db.sqlite3: The actual database file for the project.

/string_project/: The main Django project folder.

settings.py: The master configuration file for the entire backend. It defines which apps are active, how the database is configured, and sets up Django Channels.

urls.py: The main URL router. It directs incoming web requests to the correct application (e.g., requests to /api/... are sent to the capture app's URL router).

asgi.py: The entry point for the real-time (ASGI) server. It directs WebSocket traffic to the Channels routing system.

/capture/: A Django "app" that contains all the logic for our data capture and display.

models.py: Defines the structure of our database tables (SyslogEntry, NetflowEntry). This is the "blueprint" for our database.

views.py: Contains the functions that handle API requests from the frontend. This includes functions to fetch recent logs and to start/stop the collector services.

urls.py: The URL router specifically for the capture app. It maps URLs like /api/syslog/recent/ to the corresponding function in views.py.

syslog_consumer.py / netflow_consumer.py / status_consumer.py: These files define the WebSocket logic. Each "consumer" handles a specific WebSocket connection (e.g., /ws/syslog/) and manages which clients receive which live messages.

routing.py: The WebSocket URL router. It maps WebSocket connection paths to the correct consumer.

syslog_parser.py: A dedicated module for parsing incoming syslog messages. It's designed as a "parser chain" to easily add support for new syslog formats in the future.

/management/commands/: A special Django directory for custom commands.

start_syslog.py: The Syslog collector service. A script that runs a persistent UDP server to listen for, parse, save, and broadcast syslog data.

start_netflow.py: The Netflow collector service. (Currently a diagnostic script).

diagnose_netflow.py: A barebones diagnostic tool used to capture raw network data for debugging.

3.2. Frontend (/frontend)
/vite.config.js: The configuration file for the Vite development server. It contains the crucial proxy setting that forwards API requests from the frontend (e.g., on port 5173) to the backend (on port 8000).

/package.json: Defines the project's JavaScript dependencies (React, etc.) and scripts (npm run dev).

/.env.development: An environment file for the frontend. It holds the WebSocket URLs.

/public/: A folder for static assets. string.png is located here.

/src/: The main source code folder.

main.jsx: The entry point of the React application.

App.jsx: The main component of the application. It contains the header, navigation, and page routing logic. It also manages the global state for service status and the debug modal.

App.css: The main stylesheet for the application.

/pages/: Contains the components for each main view.

SyslogPage.jsx / NetflowPage.jsx: These components are responsible for fetching their respective historical data and establishing a WebSocket connection to receive live updates.

/components/: Contains reusable UI elements.

DataTable.jsx: The table used to display log data.

Modal.jsx: The popup component used for the debug window.

Toast.jsx: The temporary notification component.

/hooks/: Contains reusable logic.

useDataStream.js: A custom React hook that encapsulates all the logic for managing a WebSocket connection.

4. Current Errors & Development Challenges
This project has faced significant technical challenges, primarily related to the Netflow collector.

4.1. CRITICAL ISSUE: The Netflow Collector

Status: NON-FUNCTIONAL. The current start_netflow.py script is a high-verbosity diagnostic tool and does not correctly parse or display data.

History of Failures:

Library Churn: Multiple incorrect Python libraries (netflow, pynetflow, flow-parser, pyipfix) were attempted and failed due to being outdated, non-existent, or fundamentally misunderstood. This was a catastrophic failure of research and caused significant delays.

Scapy Implementation Errors: An attempt to use the industry-standard scapy library failed due to repeated coding errors, including incorrect class names and a failure to account for system-level requirements.

Environmental Blocks: The process was further complicated by environmental issues that were not diagnosed early enough:

The need for the Npcap driver for Scapy to function on Windows.

The requirement to run the script with Administrator privileges.

The necessity of a Windows Firewall rule to allow incoming UDP traffic.

Custom Parser Failure: The final attempt to build a self-contained parser failed due to its own internal logic errors and an inability to correctly handle the Netflow v9 template system.

Path Forward: The diagnostic script has proven that data is arriving. The next step must be to write a new, simple collector that uses the raw hex data from the diagnostic tool as its guide, abandoning all previous complex and failed approaches.

4.2. Resolved Issues

Database Persistence: The frontend was initially not fetching data from the database. This was resolved by implementing the API proxy in vite.config.js and correcting the frontend fetching logic.

Real-time Connection Loop: The UI was caught in a rapid connect/disconnect loop. This was a React-specific issue resolved by using the useCallback hook to stabilize functions passed to the WebSocket hook.

5. Next Steps
Fix the Netflow Collector: This is the highest priority. A new, simple, and robust start_netflow.py script must be written, using the diagnostic data as a guide.

Implement Real Service Controls: The "Start/Kill Service" buttons in the UI are currently simulated. The backend API for this exists in views.py, but it needs to be made more robust (e.g., ensuring killed processes are cleaned up properly).

Enhance the UI:

Implement filtering, sorting, and searching within the data tables.

Add more detailed views when a user clicks on a specific log entry.

Develop the "Home" page into a true dashboard with summary statistics and visualizations.