# Chatbot.ai Requirements

**Objective:**

The main goal of chatbot.ai is to create an easy-to-use tool that helps employees find information about HR policies and documents quickly and efficiently. By automating answers to common questions, the chatbot will reduce the workload on our HR team and make it easier for employees to get the information they need at any time. This will improve overall user experience by providing fast and accurate responses, ensuring that our employees can easily access important HR information whenever they need it. Additionally, the chatbot will be designed to grow with our organization, adapting to new policies and handling an increasing number of queries, all while keeping employee data secure and private.

**Features and Flow:**

Automated Query Resolution:
The chatbot will automatically handle and resolve common HR-related queries about policies and documents.
Real-Time Information Updates:
The chatbot will be connected to the latest HR policy and document databases, ensuring it always provides up-to-date information.
Reduced HR Workload:
By handling routine queries, the chatbot will reduce the number of repetitive tasks HR staff need to perform, allowing them to focus on more complex issues.
Data Privacy and Security:
Ensuring all interactions and data handled by the chatbot are secure and comply with organizational data privacy policies to protect employee information.


**Flow**


**Error Handling**
If the chatbot doesn’t have the answer to the question then it should reply with a meaningful message based on the question.
If the user isn’t logged then they should be asked to login first.
If a user queries for unauthorized data they should prompt them that the user try to access data which the user is not supposed to.
If unable to read the policy file it should send an email to the admin.
If folder is not accessible it should send an email to the admin

**Logging:**
Different levels, like, INFOR,DEBUG, ERROR, etc. of logging should be used to debug the problem. But in production it should be set to ERROR level.


**Scenarios:**
If the user the ask for the whole policy document it should not reply the whole document, it should ask the user to download it from hono
Should answer for the authorized content for the user.
Without login no question should be responded
Parse the document only once until it is updated.
If the document is removed from the drive then the data should also be remove the vectorDB.

## Project Setup

### Ollama Installation 

[Refer this](https://ollama.com/download)

### Llama Installation

Once Ollama is installed, open your terminal or command prompt and run:
``` ollama pull llama3.2 ```

After the model is downloaded, start using it with this simple command like `ollama list`

### Install postgres 
If you've postgres version lower than 14, upgrade it to 14 or install latest version.
For Ubuntu, [refer this](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-14-04)
For Others, [refer this](https://www.postgresql.org/download/)

### Install pgvector
[Refer this](https://github.com/pgvector/pgvector)

### Clone the repo
Clone the repository using command:
```
git clone git@github.com:joshsoftware/chatbot.ai.git 
git pull origin feature/ollama-chat
``` 
Install the requirement file using command: `pip install -r requirements.txt`

Create environment file and set db url and WebScrapping Varialbles.

