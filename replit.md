# Overview

This is an AI Bot Platform - a Flask-based web application that provides smart automation for businesses through AI-powered chatbots. The platform features user authentication, a dashboard interface for managing bot settings and conversations, and an API for chat interactions. It's designed as a SaaS solution with pricing tiers and user management capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Server-side rendered HTML templates using Jinja2
- **Styling**: TailwindCSS for responsive design with custom CSS for animations and effects
- **JavaScript**: Vanilla JavaScript for interactive features like chat functionality
- **UI Components**: Feather Icons for iconography, AOS library for scroll animations
- **Layout**: Responsive design with navigation bars, sidebars, and dashboard layouts

## Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy for database operations
- **Security**: 
  - CSRF protection via Flask-WTF
  - Password hashing using Werkzeug's security utilities
  - Session-based authentication
  - Environment-based secret key management
- **Database**: SQLite for local development (configured for easy migration to other databases)
- **API Design**: RESTful endpoints for chat interactions and user management

## Data Storage
- **Primary Database**: SQLite with SQLAlchemy ORM
- **User Model**: Stores user credentials (id, full_name, email, hashed_password)
- **Database Location**: `instance/users.db` for development
- **Migration Ready**: Architecture supports easy transition to PostgreSQL or other databases

## Authentication & Authorization
- **Session Management**: Flask sessions for user state management
- **Password Security**: Werkzeug password hashing and verification
- **CSRF Protection**: Built-in CSRF token validation for all forms
- **Environment Security**: Production-ready secret key configuration with fallback for development

## Application Structure
- **Templates**: Organized template hierarchy with base templates and component inheritance
- **Static Assets**: CSS and JavaScript files with TailwindCSS build pipeline
- **Route Organization**: Clean separation of concerns with dedicated routes for different features
- **Error Handling**: Flash message system for user feedback

# External Dependencies

## Core Framework Dependencies
- **Flask 3.0.3**: Main web framework
- **Flask-SQLAlchemy**: Database ORM integration
- **Flask-WTF 1.2.1**: CSRF protection and form handling
- **Werkzeug**: Security utilities for password hashing

## Development & Build Tools
- **TailwindCSS 3.4.14**: CSS framework for styling
- **Node.js/NPM**: For TailwindCSS build pipeline
- **Python-dotenv 1.0.1**: Environment variable management

## Frontend Libraries (CDN)
- **TailwindCSS**: CSS framework loaded via CDN
- **Feather Icons**: Icon library for UI elements
- **AOS (Animate On Scroll)**: Animation library for scroll effects

## Deployment & Production
- **Gunicorn 23.0.0**: WSGI HTTP Server for production deployment
- **Vercel**: Configured for serverless deployment
- **Requests 2.32.3**: HTTP library for external API calls

## Planned Integrations
- **AI/Chat APIs**: Architecture prepared for integration with AI services for bot functionality
- **Payment Processing**: Billing page structure ready for payment gateway integration
- **Analytics**: Analytics page structure ready for tracking integration