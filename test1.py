from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import smtplib

def send_verification_email():
    # Get email and generate OTP
    # data = request.get_json()
    email = "ompitroda55@gmail.com"
    # print(email)
    otp = str(random.randint(100000, 999999))

    # Construct HTML content for the email
    subject = 'Email Verification Mail'
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background-color: #ffffff;
            }}
            .container {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background-color: #58cc02;
                color: #ffffff;
                padding: 20px;
            }}
            .logo {{
                font-size: 2.5rem;
                font-family: 'Varela Round', sans-serif;
                font-weight: 800;
                margin-bottom: 20px;
            }}
            .subject {{
                font-size: 1.5rem;
                font-family: 'Poppins', sans-serif;
                margin-bottom: 20px;
            }}
            .text {{
                font-size: 1rem;
                font-family: 'Poppins', sans-serif;
            }}
            #email, #otp {{
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <span class="logo">LearnSync</span>
            <span class="subject">{subject}</span>
            <div class="text">Your OTP for email <span id="email">{email}</span> is <span id="otp">{otp}</span>.</div>
        </div>
    </body>
    </html>
    """.format(subject=subject, email=email, otp=otp)

    # Create MIME message
    msg = MIMEMultipart()
    msg['From'] = 'taccovan001@gmail.com'
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    # Connect to SMTP server and send email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('taccovan001@gmail.com', 'zrntrzoqwjgdhjzs')  # Update with your email password
    server.sendmail(email, email, msg.as_string())
    server.quit()

    return otp

print(send_verification_email())