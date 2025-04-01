# MGML Sample Database - Agent Guidance

## Commands
- Install: `pip install -r requirements.txt`
- Run server: `python manage.py runserver`
- Migrations: `python manage.py makemigrations && python manage.py migrate`
- Create admin: `python manage.py createsuperuser`
- Run tests: `python manage.py test sampletracking.tests`
- Run specific test: `python manage.py test sampletracking.tests.TestClassName.test_method_name`

## Code Style
- Follow PEP 8 conventions
- Imports: stdlib → Django → third-party → local (with line breaks between groups)
- Models: CamelCase classes, snake_case fields, include help_text for all fields
- Views: Class-based preferred, use LoginRequiredMixin for auth
- Docstrings: Triple quotes for all classes and functions
- Error handling: Use Django form validation wherever possible
- Indent: 4 spaces, max line length 100 characters
- Abstract base classes used for shared functionality (e.g., TimeStampedModel)
- Model field parameters vertically aligned for readability
- Add proper validators to model fields