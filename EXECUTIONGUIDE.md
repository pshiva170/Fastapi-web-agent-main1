
Execution & Testing Guide

This guide provides step-by-step instructions to set up, run, and test the "Advanced FastAPI AI Agent" on a local machine. Please follow these steps in order.

Phase 1: Environment Setup

This phase prepares your computer with all the necessary software and configurations.

Step 1: Install Prerequisites

Ensure the following software is installed and running on your system.

Python (version 3.10 or newer)

Git (for cloning the repository)

Ollama: Required for running the AI model locally. Download and install from the official Ollama website.

Redis: Required for API rate limiting. Installation instructions can be found on the Redis website.

Step 2: Clone the Repository

Open a terminal or PowerShell and clone the project from GitHub.

# Replace the URL if your repository location is different
git clone https://github.com/pshiva170/fastapi-web-agent.git

# Navigate into the newly created project folder
cd fastapi-web-agent

Step 3: Create and Activate a Python Virtual Environment

This isolates the project's dependencies from your system's Python.

# Create the virtual environment
python -m venv venv

# Activate the environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

You will know it's active when you see (venv) at the beginning of your terminal prompt.

Step 4: Install Dependencies

Install all the required Python packages using the requirements.txt file.

pip install -r requirements.txt
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
Step 5: Configure Environment Variables

The application requires a .env file for secret keys.

In the root of the project folder, create a new file named .env.

Copy the entire block below and paste it into the .env file.

Replace "your_super_secret_password_here" with a secret password of your own invention.

# .env File Template

# Invent your own secret password. This will be used in the "Authorization: Bearer <key>" header.
APP_SECRET_KEY="your_super_secret_password_here"

# OPTIONAL: To use the high-speed Groq service, add your key here.
# If left blank, the application will default to using local Ollama.
GROQ_API_KEY=

# OPTIONAL: Only change these if your local services are not running on default ports.
OLLAMA_HOST="http://localhost:11434"
REDIS_URL="redis://localhost:6379"
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Env
IGNORE_WHEN_COPYING_END
Step 6: Download the Local AI Model

For local development, the application is configured to use tinyllama. You must download this model via Ollama.

ollama pull tinyllama
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Wait for the download to complete.

Phase 2: Running the Application
Step 7: Start the FastAPI Server

Now, run the application using uvicorn. The server will automatically reload if you make any code changes.

uvicorn agent_server:app --reload
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
Step 8: Verify a Successful Start

Look for the following messages in your terminal to confirm the server started correctly:

INFO:     AI ANALYZER: Configuring to use local Ollama.
INFO:     AI ANALYZER: Connection to Ollama at http://localhost:11434 successful.
INFO:     Successfully connected to Redis for rate limiting.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

Leave this terminal window running. The server is now live.

Phase 3: Testing the API Endpoints

For this phase, open a new, separate terminal or PowerShell window. The following commands use PowerShell syntax for Windows.

Step 9: Test the /analyze Endpoint

This test will scrape stripe.com and ask two questions.

Prepare the command. Copy the entire block below into a text editor.

Replace "your_super_secret_password_here" with the same secret key you put in your .env file.

Copy the edited block and paste it into your new PowerShell window, then press Enter.

# --- Test for /analyze endpoint ---

$headers = @{
    "Content-Type"  = "application/json";
    "Authorization" = "Bearer your_super_secret_password_here"
}

$body = @'
{
    "url": "https://stripe.com",
    "questions": [
        "What industry is this company in?",
        "Who are their primary customers?"
    ]
}
'@

(Invoke-WebRequest -Uri "http://127.0.0.1:8000/analyze" -Method POST -Headers $headers -Body $body).Content | ConvertFrom-Json
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Powershell
IGNORE_WHEN_COPYING_END

Expected Output: You should receive a detailed JSON response containing Stripe's company information and answers to your questions, similar to the structure below.

{
  "url": "https://stripe.com",
  "analysis_timestamp": "...",
  "company_info": {
    "industry": "Financial Technology (FinTech)",
    "company_size": "Large Enterprise (>7000 employees)",
    "location": "San Francisco, CA & Dublin, Ireland",
    "core_products_services": [ "Payment processing", "Invoicing", "Subscription management" ],
    "unique_selling_proposition": "Stripe provides a comprehensive suite of payment APIs that powers commerce for online businesses of all sizes.",
    "target_audience": "Developers, startups, and large enterprises"
  },
  "extracted_answers": [
    {
      "question": "What industry is this company in?",
      "answer": "Stripe is in the financial technology (FinTech) industry, providing economic infrastructure for the internet."
    }
  ]
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
Additional Test Cases

Here are more examples to test the application's versatility. Remember to replace the placeholder for the secret key in the $headers variable for each command.

Test Case 1: Analysis Without Custom Questions

This test checks the API's ability to handle requests where the optional questions field is omitted.

Command (PowerShell):

$headers = @{ "Content-Type" = "application/json"; "Authorization" = "Bearer your_super_secret_password_here" }
$body = @'
{
    "url": "https://fastapi.tiangolo.com/"
}
'@
(Invoke-WebRequest -Uri "http://127.0.0.1:8000/analyze" -Method POST -Headers $headers -Body $body).Content | ConvertFrom-Json
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Powershell
IGNORE_WHEN_COPYING_END

Expected Output: The response should contain the full company_info block but have an empty list for extracted_answers.

{
  "url": "https://fastapi.tiangolo.com/",
  "analysis_timestamp": "...",
  "company_info": {
    "industry": "Open-Source Software / Web Development Framework",
    "company_size": "N/A",
    "location": "N/A",
    "core_products_services": ["A modern, fast web framework for building APIs with Python."],
    "unique_selling_proposition": "FastAPI is a high-performance web framework for building APIs with Python based on standard Python type hints.",
    "target_audience": "Python developers"
  },
  "extracted_answers": []
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
Test Case 2: Conversational Follow-up

This test demonstrates the /chat endpoint's ability to answer a natural language follow-up question.

Command (PowerShell):

$headers = @{ "Content-Type" = "application/json"; "Authorization" = "Bearer your_super_secret_password_here" }
$body = @'
{
    "url": "https://www.mongodb.com/",
    "query": "What is MongoDB Atlas and who is it for?"
}
'@
(Invoke-WebRequest -Uri "http://127.0.0.1:8000/chat" -Method POST -Headers $headers -Body $body).Content | ConvertFrom-Json
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Powershell
IGNORE_WHEN_COPYING_END

Expected Output: A conversational response that directly answers the user's query.

{
  "url": "https://www.mongodb.com/",
  "user_query": "What is MongoDB Atlas and who is it for?",
  "agent_response": "MongoDB Atlas is the company's fully-managed cloud database service. It is designed for developers who want to build applications without having to worry about managing the underlying database infrastructure, handling things like backups, scaling, and security automatically.",
  "context_sources": [ "Homepage Text Content" ]
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
Test Case 3: Handling a Non-Corporate Website

This test shows how the system behaves when given a URL that is not a standard company homepage, like a Wikipedia article.

Command (PowerShell):

$headers = @{ "Content-Type" = "application/json"; "Authorization" = "Bearer your_super_secret_password_here" }
$body = @'
{
    "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"
}
'@
(Invoke-WebRequest -Uri "http://127.0.0.1:8000/analyze" -Method POST -Headers $headers -Body $body).Content | ConvertFrom-Json
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Powershell
IGNORE_WHEN_COPYING_END

Expected Output: The model should correctly identify that company-specific fields do not apply and fill them with "N/A", demonstrating robustness.

{
  "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
  "analysis_timestamp": "...",
  "company_info": {
    "industry": "Information / Encyclopedia",
    "company_size": "N/A",
    "location": "N/A",
    "core_products_services": [ "Information about the Python programming language." ],
    "unique_selling_proposition": "A free, collaborative online encyclopedia containing information on a wide variety of topics.",
    "target_audience": "General public, researchers, students"
  },
  "extracted_answers": []
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END


IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
