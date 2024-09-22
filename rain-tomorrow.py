import requests
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# API Key for OpenWeatherMap and location coordinates
API_KEY = os.getenv('API_KEY')
LATITUDE = os.getenv('LATITUDE')
LONGITUDE = os.getenv('LONGITUDE')
EMAIL = os.getenv('EMAIL')
APP_PASSWORD = os.getenv('APP_PASSWORD')

def get_weather_forecast():
    # Get the weather forecast for the next day using the 5 Day / 3 Hour Forecast API
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY}&units=imperial"
    
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error fetching weather data: {response.status_code} - {response.text}")
        return None

    data = response.json()
    forecasts = data['list']
    
    # Get tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    
    # Store detailed weather data for tomorrow
    weather_report = []
    
    # Check for weather data for tomorrow
    for forecast in forecasts:
        forecast_time = forecast['dt_txt']
        forecast_date = datetime.strptime(forecast_time, "%Y-%m-%d %H:%M:%S").date()
        
        if forecast_date == tomorrow:
            # Extract weather details
            weather_main = forecast['weather'][0]['main']
            description = forecast['weather'][0]['description']
            temperature = forecast['main']['temp']
            humidity = forecast['main']['humidity']
            wind_speed = forecast['wind']['speed']
            
            # Store detailed weather information for each 3-hour period
            weather_report.append({
                'time': forecast_time,
                'main': weather_main,
                'description': description,
                'temperature': temperature,
                'humidity': humidity,
                'wind_speed': wind_speed
            })
            
            # Check if rain is expected during this period
            if "rain" in weather_main.lower() or "rain" in description.lower():
                print(f"Rain forecasted at {forecast_time}: {description}")
    
    return weather_report

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    
    try:
        # Using Gmail's SMTP server for SSL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL, APP_PASSWORD)
            smtp.sendmail(EMAIL, EMAIL, msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def create_weather_report(weather_report):
    # Create a detailed weather report from the data
    email_body = "Detailed Weather Forecast for Tomorrow:\n\n"
    
    for report in weather_report:
        time = report['time']
        main_weather = report['main']
        description = report['description']
        temperature = report['temperature']
        humidity = report['humidity']
        wind_speed = report['wind_speed']
        
        email_body += f"Time: {time}\n"
        email_body += f"Weather: {main_weather} ({description})\n"
        email_body += f"Temperature: {temperature}°C\n"
        email_body += f"Humidity: {humidity}%\n"
        email_body += f"Wind Speed: {wind_speed} m/s\n"
        email_body += "-" * 40 + "\n"
    
    return email_body

def check_rain_forecast():
    # Get the weather report
    weather_report = get_weather_forecast()
    
    if weather_report:
        # Create the detailed weather report
        email_body = create_weather_report(weather_report)
        
        # Check if rain is in the forecast
        rain_expected = any('rain' in report['main'].lower() for report in weather_report)
        
        if rain_expected:
            subject = "Weather Alert: Rain Expected Tomorrow"
            # Send email with detailed weather report
            send_email(subject, email_body)
        
    else:
        print("No weather data available for tomorrow.")

if __name__ == "__main__":
    check_rain_forecast()
