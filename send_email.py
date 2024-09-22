import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def test_send_email():
    try:
        smtp_server = 'smtp.gmail.com'
        smtp_port = 465
        sender_email = '420206@student.nitandhra.ac.in'
        sender_password = 'LLLggg@123'  # Consider using environment variables for security

        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = 'rahulkabali2001@gmail.com'
        msg['Subject'] = "Test Email"

        body = "This is a test email."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, 'rahulkabali2001@gmail.com', msg.as_string())
        server.quit()

        print("Test email sent successfully!")
    except Exception as e:
        print(f"Failed to send test email. Error: {e}")

# Call the test function
test_send_email()
