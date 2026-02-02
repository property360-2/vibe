# Vibe: Academic Management System

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-5.0%2B-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

**Vibe** is a robust, Django-based Academic Management System designed to streamline educational administration. It provides a centralized platform for managing courses, subjects, and academic performance tracking through an intuitive, role-based interface.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
- [Extra Notes](#extra-notes)

---

## Features

- **Multi-Role Dashboards**: Personalized experiences for Administrators, Faculty, and Students.
- **Role-Based Permissions**: Granular access control ensuring data security and privacy.
- **Course & Subject Management**: Effortless creation and organization of academic curriculums.
- **Academic Tracking**: Comprehensive monitoring of student progress and performance metrics.
- **JWT Authentication**: Secure API access and user authentication.
- **Responsive Design**: Elegant UI that works seamlessly across all devices.

---

## Tech Stack

- **Backend**: [Django](https://www.djangoproject.com/) (Python)
- **Database**: [SQLite](https://sqlite.org/) (Development)
- **Authentication**: JWT (JSON Web Tokens)
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap 5)

---

## Installation

Follow these steps to set up the project locally.

### 1. Prerequisites
- Python 3.8 or higher installed.
- `pip` (Python package manager).

### 2. Clone the Repository
```bash
git clone https://github.com/property360-2/vibe.git
cd vibe
```

### 3. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Database Migrations
```bash
python manage.py migrate
```

---

## Usage

To start the development server, run:

```bash
python manage.py runserver
```

Once the server is running, access the application at `http://127.0.0.1:8000`.

> [!TIP]
> Use `python manage.py createsuperuser` to create an administrative account for full access.

---

## Screenshots

| Dashboard View | Management Panel |
| :---: | :---: |
| ![Dashboard Placeholder](https://via.placeholder.com/400x250?text=Student+Dashboard) | ![Management Placeholder](https://via.placeholder.com/400x250?text=Admin+Panel) |
| *Clean, data-driven student dashboard* | *Powerful administrative tools* |

---

## Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Extra Notes

- **Customization**: The UI themes can be adjusted in the `static/css` directory.
- **Scaling**: While it uses SQLite for development, it can be easily migrated to PostgreSQL for production environments.
- **Author**: Jun Alvior

---
Built for better academic management.
