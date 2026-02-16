# Meal Planner

A collaborative meal planning application built with Flask. Plan meals for the week, manage recipes, and generate shopping lists.

## Setup

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository
```bash
cd meal-planner
```

2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run the application
```bash
python run.py
```

The app will be available at `http://localhost:5000`

## Project Structure

```
meal-planner/
├── app/
│   ├── __init__.py           # App factory
│   ├── models.py             # Database models
│   ├── forms.py              # WTForms forms
│   ├── auth.py               # Authentication routes
│   ├── main.py               # Main routes
│   └── templates/
│       ├── base.html         # Base template
│       ├── home.html         # Landing page
│       ├── index.html        # Dashboard
│       └── auth/
│           ├── login.html    # Login page
│           └── register.html # Registration page
├── config.py                 # Configuration
├── run.py                    # Entry point
├── requirements.txt          # Dependencies
└── README.md
```

## Development Notes

- The app uses SQLite for the database (suitable for development)
- Authentication is required for most features
- CSRF protection is enabled for all forms
- Passwords are securely hashed using Werkzeug
