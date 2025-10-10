# simple_email_sender.py
import smtplib, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SimpleEmailSender:
    def __init__(self):
        # ВСТАВЬТЕ СВОИ ДАННЫЕ ЗДЕСЬ
        self.config = {
            'email': 'your_email@gmail.com',      # Ваш email
            'password': 'your_app_password',      # Пароль приложения
            'smtp_server': 'smtp.gmail.com',     # SMTP сервер
            'smtp_port': 587,                    # Порт
            'default_to': 'recipient@example.com' # Получатель по умолчанию
        }
        
    def generate_random(self):
        generated_code=""
        for i in range(10):
            generated_code += str(random.randint(0,9)) 
        
        return generated_code
        print(generated_code)

    def send_email(self, subject, message, to_email=None):
        """Простая отправка email"""
        if to_email is None:
            to_email = self.config['default_to']
        
        try:
            # Создание сообщения
            msg = MIMEMultipart()
            msg['From'] = self.config['email']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # Отправка
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['email'], self.config['password'])
            server.send_message(msg)
            server.quit()
            
            return True, f"Письмо отправлено для {to_email}"
        
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

# Использование:
if __name__ == '__main__':
    
    sender = SimpleEmailSender()
    

    # Просто отправляем письмо
    success, result = sender.send_email(
        subject="Тестовое письмо",
        
        message=sender.generate_random()
    )
    
    print(result)