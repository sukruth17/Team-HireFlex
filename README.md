# Crime Data Mining and Legal Advisor

A Django-based application designed for crime data analysis and providing legal advice using advanced AI-powered tools like **LLMWare**.

## Features

- **Crime Data Mining**: Analyze crime trends and patterns with data mining techniques.
- **Legal Advisor**: Get AI-powered legal advice using **LLMWare** integration.

## Installation and Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd crime-data-mining-legal-advisor
python -m venv env
source env/bin/activate  # On Windows, use `env\Scripts\activate`
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
Usage
Open your browser and navigate to http://127.0.0.1:8000/ to access the application.
Explore features like:

Crime data visualization
Legal consultation

Project Structure

legal_advisor: 
Contains the integration with LLMWare for providing legal advice.
crime_data: 
Handles crime data analysis and visualization features.
