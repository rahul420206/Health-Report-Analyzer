import asyncio
from flask import Flask, request, jsonify, render_template
import os
from utils import extract_text_from_pdf, extract_key_points, extract_test_results
from crewai import Agent, Task
import cohere
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import request, render_template
from flask import session
from flask import Flask

import cohere

co = cohere.Client("evLatt2FuOBOJti8orWXbEoATx0NDUTGAkLcXRJO")

import os

print("COHERE_API_KEY:", os.getenv("COHERE_API_KEY"))



os.environ["COHERE_API_KEY"] = "evLatt2FuOBOJti8orWXbEoATx0NDUTGAkLcXRJO"  
co = cohere.Client(os.environ["COHERE_API_KEY"])

app = Flask(__name__)

researcher = Agent(
    role='Health Analyst',
    goal='Analyze blood test data and generate recommendations.',
    backstory='You are a health analysis assistant.',
    verbose=True,
    chat_model=cohere,
    allow_delegation=False
)

article_retriever = Agent(
    role='Health Researcher',
    goal='Retrieve health-related articles based on the analysis of the user’s blood report.',
    backstory='You are responsible for finding relevant health articles based on medical information.',
    verbose=True,
    chat_model=cohere,
    allow_delegation=True 
)

web_search_agent = Agent(
    role='Web Search Expert',
    goal='Automate health-related searches based on the user’s health report and provide useful articles.',
    backstory='You specialize in retrieving relevant articles from the web.',
    verbose=True,
    chat_model=cohere,
    allow_delegation=False
)

task1 = Task(
    description='Analyze blood test data extracted from the PDF.',
    agent=researcher,
    chat_model=cohere,
    expected_output='Health recommendations based on the analysis.'
)

task2 = Task(
    description='Retrieve articles relevant to the user’s health profile based on blood test results.',
    agent=article_retriever,
    chat_model=cohere,
    expected_output='A list of health-related articles based on the report analysis.'
)

task3 = Task(
    description='Perform web search to retrieve health-related articles.',
    agent=web_search_agent,
    chat_model=cohere,
    expected_output='Links to relevant health articles.'
)

def send_email(recipient_email, report_analysis, articles):
    try:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        sender_email = '9201156@student.nitandhra.ac.in'
        sender_password = 'xffd kfub dsix aawt'  

        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Your Health Report and Related Articles"

        email_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Your Health Report Analysis:</h2>
            <p>{report_analysis}</p>
            <h2>Related Health Articles:</h2>
            {articles}
        </body>
        </html>
        """
        msg.attach(MIMEText(email_body, 'html'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        print("Email sent successfully!")

    except Exception as e:
        print(f"Failed to send email. Error: {e}")

async def generate_response(prompt):
    """Generates a response using Cohere's API."""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: co.generate(
                model="command-r-plus",
                prompt=prompt,
                max_tokens=500  
            )
        )
        return response.generations[0].text
    except Exception as e:
        return f"Error generating response: {e}"

async def analyze_blood_test(extracted_text):
    """Analyze blood test and generate refined recommendations."""
    prompt = (
        f"Analyze this blood test data in detail: {extracted_text}. "
        f"Provide structured bullet points for health recommendations, ensuring clarity and conciseness."
    )
    result = await generate_response(prompt)

    key_points = extract_key_points(result)
    bullet_points = '<ul><li>' + '</li><li>'.join(key_points) + '</li></ul>'
    return bullet_points

async def retrieve_health_articles(report_details):
    """Retrieve health articles based on provided report details."""
    prompt = (
        f"Retrieve relevant health articles with their titles and URLs based on the following report: {report_details}. "
        f"Please provide the results in the following format: 'Title: <article title>, URL: <link>'"
    )
    
    result = await generate_response(prompt)
    
    articles = result.split('\n')
    unique_articles = set()  # To avoid duplicates
    formatted_articles = ''
    
    for article in articles:
        if "Title:" in article and "URL:" in article:
            title = article.split('Title: ')[1].split(', URL:')[0].strip()
            url = article.split('URL: ')[1].strip()
            if (title, url) not in unique_articles:  # Check for duplicates
                unique_articles.add((title, url))
                formatted_articles += f'<li><a href="{url}" target="_blank">{title}</a></li>'
    
    return f'<ul>{formatted_articles}</ul>' if formatted_articles else 'No articles were retrieved.'

@app.route('/email_report', methods=['POST'])
def email_report():
    # Retrieve the email from the form
    email = request.form.get('email')

    # Retrieve extracted text from session, or provide default text if not found
    extracted_text = session.get('extracted_text', "Your blood test report details here")

    if not extracted_text:
        return "No extracted text found. Please upload the report again.", 400

    # Analyze blood test results and retrieve related health articles
    recommendations = asyncio.run(analyze_blood_test(extracted_text))
    articles = asyncio.run(retrieve_health_articles(extracted_text))

    # Check if articles were retrieved
    if not articles:
        articles = "No articles were retrieved."

    # Prepare the email body with both recommendations and articles
    email_body = f"""
    <html>
    <head></head>
    <body>
        <p> Hi!, These are the articles related to your report. Thank you!
        <br>
        <p>Note: The recommendations and articles provided are for informational purposes only. Please consult a healthcare professional for detailed medical advice.</p>
    </body>
    </html>
    """

    # Send the email with recommendations and articles
    send_email(email, email_body, articles)

    return "Email sent successfully!"

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handles PDF upload and analysis."""
    if 'pdf_file' not in request.files:
        return "No file part", 400

    file = request.files['pdf_file']
    pdf_path = os.path.join('uploads', file.filename)
    file.save(pdf_path)

    extracted_text = extract_text_from_pdf(pdf_path)
    if extracted_text is None:
        return "Failed to extract text from the PDF.", 400

    test_results = extract_test_results(extracted_text)

    within_limits = [result for result in test_results if float(result[1]) >= result[3] and float(result[1]) <= result[4]]
    out_of_limits = [result for result in test_results if float(result[1]) < result[3] or float(result[1]) > result[4]]

    recommendations = asyncio.run(analyze_blood_test(extracted_text))

    health_articles = asyncio.run(retrieve_health_articles(extracted_text))

    return render_template("results.html", recommendations=recommendations, within_limits=within_limits, out_of_limits=out_of_limits, health_articles=health_articles)

@app.route('/results')
def results():
    report_analysis = "Your personalized health report analysis here..."
    articles = retrieve_health_articles()

    return render_template('results.html', analysis=report_analysis, articles=articles)

from flask import session, request
from flask_session import Session  

if __name__ == "__main__":
    os.makedirs('uploads', exist_ok=True)  
    app.run(debug=True)