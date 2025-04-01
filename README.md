# MGML Sample Database

A Django-based application for tracking samples in the MGML laboratory as they move through different processing stages.

## Features

- Track samples through their entire lifecycle:
  - Crude Samples
  - Aliquots
  - Extracts
  - Sequence Libraries
- Dashboard with visualizations and statistics
- Search capabilities across all sample types
- User authentication and sample ownership tracking
- Detailed sample history and audit trail

## Project Structure

- `mgml_sampledb/` - Main project directory
  - `settings.py` - Project settings
  - `urls.py` - Project URL configuration
- `sampletracking/` - Main application
  - `models.py` - Database models
  - `views.py` - Views and request handlers
  - `forms.py` - Form definitions
  - `admin.py` - Admin interface configuration
  - `templates/` - HTML templates
    - `base_generic.html` - Base template
    - `sampletracking/` - App-specific templates

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mgml_sampledb.git
   cd mgml_sampledb
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   DB_NAME=mgml_sampledb
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

5. Run migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

8. Access the application at http://localhost:8000

## Usage

1. Log in using your credentials
2. Navigate to the dashboard to see an overview of samples
3. Add new samples using the appropriate forms
4. Search for samples using the search bar
5. View, edit, and process samples through their lifecycle

## Technology Stack

- Django 5.0
- MySQL
- Bootstrap 4
- jQuery
- Chart.js (for dashboard visualizations)

## Contributors

- Your Name - Initial work

## License

This project is licensed under the MIT License - see the LICENSE file for details.
