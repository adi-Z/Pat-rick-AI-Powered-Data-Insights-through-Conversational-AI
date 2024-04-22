# Pat-rick: AI Powered Data Insights through Conversational AI

Pat-rick is a capstone project of BISI students at Algonquin College working with CanadaPost. This project integrates Local LLM (Ollama) and OpenAI's LLM with a Streamlit web application to provide a comprehensive interactive experience for data querying and visualization.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- You have installed Python 3.8 or higher.
- You have a basic understanding of Python projects.
- You have MySQL or PostgreSQL installed if using a database.

## Configuration

**Database Configuration:**
- Ensure your database is running and accessible.
- Configure the database URI in the application settings or as an environment variable.
- For local LLM, use data file to create local database.

**API Keys:**
- Obtain your API keys for OpenAI's services.
- Set the API keys in your environment variables or directly in the application settings.

## Usage

To run the Streamlit application, execute the following command:

`streamlit run app.py`

This command starts the web server and opens the Streamlit application in your default web browser. Interact with the application GUI to input queries and view results.

## Features

**Interactive LLM Queries:**
  - Use OpenAI's LLM for generating SQL queries from natural language.
  - Local LLM support for additional query processing and enhancements.

**Dynamic Visualizations:**
  - Automatically generate charts and graphs based on query results.
  - Utilize matplotlib and seaborn for visual outputs.

**Streamlit Integration:**
  - A user-friendly web interface.
  - Easy to use widgets for interactive inputs.


## Troubleshooting

**Dependency Issues:**
  - Ensure all dependencies are installed within the same virtual environment to avoid conflicts.
  - Check the versions if there's an issue, refer to `requirements.txt` for the correct versions.

## Contributors
Thanks to all contributors!

- Salwa Mehreen​
- Arit Akpan
- Eduardo Manotas
- Esin Bilgin Savkli
- Julia Saavedra​
