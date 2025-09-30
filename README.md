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
- **Hierarchical Sample Tracking System**:
  - Parent Samples (formerly "Crude Samples") with Subject ID validation
  - Aliquots (derived from parent samples)
  - Extracts (derived from aliquots)
  - Sequence Libraries (derived from extracts, with 45+ library prep methods)
  - Plates (96-well format)
- **Sample ID System**: Automatic generation of unique, hierarchical IDs
  - Format: `{SourceType}-{Date}-{Seq}-{SampleType}`
  - Example: `IS-250919-001-CS` for isolate parent sample
  - Sample types: CS (Parent Sample), AL (Aliquot), EX (Extract), SL (Sequence Library)
- **Barcode Validation System**:
  - Automatic validation that barcode starts with Subject ID
  - Override option for generic pre-printed barcodes
  - Full audit trail of validation overrides
- **Project & Study Tracking**:
  - Project name, investigator, patient group, and study ID fields
  - Advanced filtering and reporting by project metadata
  - Support for legacy sample imports with preserved metadata
- **Advanced Filtering & Reporting**:
  - Web-based advanced filter interface (`/advanced-filter/`)
  - Filter by sample type, date range, project, investigator, patient group
  - Multiple export formats: View, CSV, Label Printing
  - Bulk selection across paginated results
- **Legacy Sample Import System**:
  - Import thousands of historical samples from CSV
  - Preserves original sequence filenames for metadata crosswalk
  - Auto-generates full sample hierarchy
  - Management command: `python manage.py import_legacy_samples`
- **Sequence Library Management**:
  - 45+ library preparation methods across 5 categories
  - Automatic sequence filename generation
  - Support for legacy filename preservation
  - Library type filtering and reporting
- **Role-Based Access Control**:
  - Sample Collectors: Can only register new samples
  - Viewers: Read-only access
  - Technicians: Can add and modify samples
  - Lab Managers: Full access including delete permissions
- **Mobile-Optimized Collection Portal** at `/collection/`
- **Dashboard** with visualizations and statistics
- **Complete Audit Trail** tracking who did what and when
- **Storage Location Tracking** (Freezer/Shelf/Box, with support for both boxes and plates)

## Project Structure

- `mgml_sampledb/` - Main project directory
  - `settings.py` - Project settings
  - `urls.py` - Project URL configuration
- `sampletracking/` - Main application
  - `models.py` - Database models with hierarchical sample tracking
  - `views.py` - Class-based views and request handlers
  - `forms.py` - Form definitions with validation
  - `admin.py` - Custom admin interface configuration
  - `templates/` - HTML templates
    - `base_generic.html` - Base template with navigation
    - `sampletracking/` - App-specific templates:
      - `home.html` - Main landing page
      - `advanced_filter.html` - Advanced filtering interface
      - `*_list.html` - List views for each sample type
      - `*_detail.html` - Detail views for each sample type
      - `*_form.html` - Creation/edit forms
      - `quick_aliquot_form.html` - Quick create workflow
  - `management/commands/` - Custom Django management commands
    - `import_legacy_samples.py` - Legacy sample import command
    - `setup_groups.py` - User group setup command
  - `migrations/` - Database migration files
- `static/` - Static files (CSS, JavaScript, images)
  - `js/sample_selection.js` - Sample selection management across pagination
  - `images/` - MGML branding and logos
- `migration_backup/` - Backup of old migrations
- `reports/` - Generated CSV reports
- Configuration files:
  - `requirements.txt` - Python dependencies
  - `.env` - Environment variables (not in version control)
  - `CLAUDE.md` - AI assistant guidance
  - `PROJECT_STATUS.md` - Detailed project status and TODO list
  - `restart_gunicorn.sh` - Server restart script

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
1. **Receiving Samples**:
   - Access the main portal and click "Receive Sample"
   - Scan or enter the barcode of the incoming sample
   - Verify sample information
   - Enter storage location (Freezer/Shelf/Box)
   - Confirm receipt - sample status changes to "Available"

2. **Creating Sample Derivatives**:
   - **Quick Create**: Use "Quick Create" for rapid aliquot creation with parent sample
   - **Standard Workflow**: Create aliquots → extracts → sequence libraries in sequence
   - All samples automatically inherit base_id and receive unique sample_id

3. **Advanced Filtering & Reports**:
   - Navigate to "Advanced Filter & Export" from home page or Reports section
   - Filter by sample type, date range, project metadata, or sample source
   - Select specific samples across multiple pages using checkboxes
   - Export results as CSV or label-printing format
   - View comprehensive reports with all sample details

### General Usage
1. **Home Page**: Quick access to all sample creation forms and reports
2. **Sample Lists**: View all samples by type (Parent Samples, Aliquots, Extracts, Libraries)
3. **Search**: Use quick search bar or advanced filtering for complex queries
4. **Sample Details**: Click any sample to view:
   - Complete metadata and storage location
   - Parent-child relationships
   - Historical changes (audit trail)
   - Derived samples (e.g., aliquots from a parent sample)
5. **Bulk Operations**: Select multiple samples for batch export or labeling

### Admin Interface
- Access at `/admin/` with staff credentials
- Custom admin interface with MGML branding
- Features:
  - Bulk actions for sample management
  - Advanced filtering and search
  - Export capabilities
  - Historical data viewing (via Django Simple History)
  - User and group management
  - Override indicators for barcode validation

## Sample Sources & Types

### Available Sample Sources
The system supports 8 sample source types with automatic ID prefixes:
1. **Stool (ST)** - Fecal samples
2. **Oral Swab (OR)** - Oral cavity samples
3. **Nasal Swab (NA)** - Nasal cavity samples
4. **Skin Swab (SK)** - Skin surface samples
5. **Blood (BL)** - Blood samples
6. **Tissue (TI)** - Tissue biopsies
7. **Isolate (IS)** - Bacterial isolates (with optional isolate source tracking)
8. **Other (OT)** - Other sample types

### Isolate Source Tracking
For samples with source type "Isolate", additional tracking of isolation source:
- Blood
- Urine
- Wound
- Stool
- Laboratory
- Other

### Library Preparation Methods
45+ sequencing library preparation methods organized by category:
- **Metagenomics**: Nextera XT, TruSeq Shotgun, Swift Accel-NGS, etc.
- **Metatranscriptomics**: TruSeq Stranded Total RNA, Kapa RNA HyperPrep, etc.
- **Bulk RNA-seq**: TruSeq mRNA, Clontech SMARTer, etc.
- **Single-cell RNA-seq**: 10x Genomics 3'/5' Gene Expression, Drop-seq, etc.
- **Specialized RNA-seq**: Oxford Nanopore Direct RNA, PacBio Iso-Seq, etc.

Each method has a unique 2-letter suffix for filename generation (e.g., NX for Nextera XT).

## Technology Stack

- **Backend**: Django 5.1.12 (security-patched) with Django Simple History 3.10.1 for audit trails
- **Database**: MySQL with full transaction support and mysqlclient 2.2.1
- **Frontend**: Bootstrap 4 (mobile-responsive) with crispy-bootstrap4 forms
- **JavaScript**: jQuery with real-time form validation and sample selection management
- **Web Server**: Gunicorn 23.0.0 for production deployment
- **Security**: Role-based permissions, CSRF protection, secure session management, CORS headers
- **Compliance**: Audit logging, user tracking, data integrity controls, historical record tracking
- **Additional Features**:
  - Django Filter 23.5 for advanced filtering
  - Pillow 10.4.0 for image handling
  - Python Decouple 3.8 for environment configuration

## Management Commands

### Import Legacy Samples
Import historical samples from CSV files:
```bash
python manage.py import_legacy_samples <csv_file> [options]
```

**Options**:
- `--dry-run`: Preview import without making changes
- `--skip-intermediates`: Skip creating intermediate aliquots/extracts
- `--username <username>`: Specify user for audit trail (default: admin)

**CSV Format**:
The import system expects a CSV file with the following columns:
- **Required**: `subject_id`, `collection_date`
- **Optional**: `legacy_sequence_filename`, `project_name`, `investigator`, `patient_type`, `study_id`, `sample_source`, `isolate_source`, `barcode`, `n_index`, `s_index`, `library_type`, `sequencing_date`, `sequencing_platform`, `notes`, `data_file_location`

See `import_template.csv` for a complete example.

**Import Behavior**:
- Creates full sample hierarchy: Parent Sample → Aliquot → Extract → Sequence Library
- Auto-generates barcodes with suffixes (_CR, _AL, _EX, _SL) if not provided
- Preserves original sequence filenames for metadata crosswalk
- Marks imported samples with status='ARCHIVED'
- Validates data and reports errors before importing

### Other Management Commands
```bash
# Set up user groups and permissions
python manage.py setup_groups

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run tests
python manage.py test sampletracking.tests
```

## Key URLs

### Main Application
- `/` - Home page with quick access to all features
- `/search/` - Quick search functionality
- `/dashboard/` - Dashboard with statistics and visualizations

### Sample Management
- `/crude-samples/` - List all parent samples
- `/crude-samples/create/` - Create new parent sample
- `/aliquots/` - List all aliquots
- `/aliquots/create/` - Create new aliquot
- `/aliquots/quick-create/` - Quick create parent sample + aliquot
- `/extracts/` - List all extracts
- `/extracts/create/` - Create new extract
- `/libraries/` - List all sequence libraries
- `/libraries/create/` - Create new sequence library

### Reports & Filtering
- `/advanced-filter/` - Advanced filtering and export interface
- `/comprehensive-report/` - Comprehensive report generation

### Sample Collection & Receiving
- `/collection/` - Collection portal (mobile-optimized)
- `/accessioning/` - Register new sample (collection staff)
- `/find-sample/` - Find and receive sample (lab staff)

### Administration
- `/admin/` - Django admin interface

## Recent Updates

### Version: September 2025

**Major Features Added**:
- **Bulk Selection System**: Select samples across multiple pages for batch operations
- **Advanced Filtering Interface**: Comprehensive filtering by project, investigator, patient group, sample type, and date ranges
- **Legacy Sample Import**: Management command to import thousands of historical samples with metadata preservation
- **Sample ID System**: Automatic generation of hierarchical sample IDs (format: `{SourceType}-{Date}-{Seq}-{SampleType}`)
- **Sequence Library Management**: 45+ library preparation methods with automatic filename generation
- **Project & Study Tracking**: Track project name, investigator, patient group, and study ID across all samples
- **Quick Create Workflow**: Rapid parent sample + aliquot creation in one step
- **Isolate Source Tracking**: Additional metadata for bacterial isolate samples

**UI/UX Improvements**:
- Renamed "Crude Sample" to "Parent Sample" throughout the interface
- Reorganized home page with Reports section prominently displayed
- Enhanced list views with concentration data for extracts
- Updated terminology: "Patient Type" → "Patient Group"
- Mobile-responsive design improvements

**Technical Updates**:
- Security patch: Updated Django from 5.0 to 5.1.12
- Added JavaScript-based sample selection management
- Improved export formats (CSV, label printing)
- Enhanced barcode validation with override tracking

## Contributors

- David Haslam (dbhaslam@gmail.com)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support & Documentation

For detailed project status, TODO list, and recent changes, see:
- `PROJECT_STATUS.md` - Current status and development roadmap
- `CLAUDE.md` - Development guidelines and code standards
- `DEPLOYMENT.md` - Production deployment instructions (if available)
- `SECURITY_CHECKLIST.md` - Security best practices (if available)
