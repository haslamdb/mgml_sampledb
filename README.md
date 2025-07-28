# MGML Sample Database

A GLP & CLIA compliant Django-based application for tracking samples in the MGML (Microbial Genomics & Metagenomics Laboratory) as they move through different processing stages.

## Compliance & Features

### Regulatory Compliance
- **GLP (Good Laboratory Practice) Compliant**: Full audit trail with user tracking and timestamps
- **CLIA (Clinical Laboratory Improvement Amendments) Compliant**: Proper sample tracking and chain of custody
- **21 CFR Part 11 Ready**: Electronic signatures and audit trails via Django Simple History

### Core Features
- **Two-Step Sample Registration Workflow**:
  - Step 1: Collection staff register samples (status: "Awaiting Receipt")
  - Step 2: Lab staff receive and store samples (status: "Available")
- **Sample Lifecycle Tracking**:
  - Crude Samples (with Subject ID validation)
  - Aliquots
  - Extracts
  - Sequence Libraries
  - Plates (96-well format)
- **Barcode Validation System**:
  - Automatic validation that barcode starts with Subject ID
  - Override option for generic pre-printed barcodes
  - Full audit trail of validation overrides
- **Role-Based Access Control**:
  - Sample Collectors: Can only register new samples
  - Viewers: Read-only access
  - Technicians: Can add and modify samples
  - Lab Managers: Full access including delete permissions
- **Mobile-Optimized Collection Portal** at `/collection/`
- **Dashboard** with visualizations and statistics
- **Advanced Search** capabilities across all sample types
- **Complete Audit Trail** tracking who did what and when
- **Storage Location Tracking** (Freezer/Shelf/Box)

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
   sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config
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

7. Set up user groups and permissions:
   ```
   python manage.py setup_groups
   ```
   This creates the following groups:
   - **Sample Collectors**: For nurses/collection staff
   - **Viewers**: Read-only access
   - **Technicians**: Standard lab users
   - **Lab Managers**: Full administrative access

8. Run the development server:
   ```
   python manage.py runserver
   ```

9. Access the application at http://localhost:8000

> **💡 Pro Tip**: After initial setup, see `VIRTUAL_ENVIRONMENT_GUIDE.md` for convenient ways to work with the project, including the `mgml` alias that combines `cd` and virtual environment activation!

## Usage

### For Sample Collection Staff
1. Access the collection portal at `/collection/` or via the home page
2. Click "Register New Sample"
3. Enter the Subject ID and scan the barcode
   - The system validates that the barcode starts with the Subject ID
   - Use the override checkbox for generic pre-printed barcodes
4. Fill in collection details and submit
5. Sample is marked as "Awaiting Receipt"

### For Lab Staff
1. Access the main portal and click "Receive Sample"
2. Scan or enter the barcode of the incoming sample
3. Verify sample information
4. Enter storage location (Freezer/Shelf/Box)
5. Confirm receipt - sample status changes to "Available"

### General Usage
1. Use the dashboard to view sample statistics and recent activity
2. Search for samples using the search bar
3. Create aliquots, extracts, and sequence libraries from existing samples
4. Track samples through their entire lifecycle
5. View complete audit history for any sample

### Admin Interface
- Access at `/admin/` with staff credentials
- Custom admin interface with MGML branding
- Features:
  - Bulk actions for sample management
  - Advanced filtering and search
  - Export capabilities
  - Historical data viewing
  - User and group management
  - Override indicators for barcode validation

## Technology Stack

- **Backend**: Django 5.0 with Django Simple History for audit trails
- **Database**: MySQL with full transaction support
- **Frontend**: Bootstrap 4 (mobile-responsive)
- **JavaScript**: jQuery with real-time form validation
- **Visualizations**: Chart.js for dashboard analytics
- **Security**: Role-based permissions, CSRF protection, secure session management
- **Compliance**: Audit logging, user tracking, data integrity controls

## Contributors

- David Haslam (dbhaslam@gmail.com)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
