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

def get_time_period(hour):
    """Convert hour to human-readable time period based on 3-hour intervals."""
    if 0 <= hour < 3:
        return "late night"
    elif 3 <= hour < 6:
        return "early morning"
    elif 6 <= hour < 9:
        return "morning"
    elif 9 <= hour < 12:
        return "late morning"
    elif 12 <= hour < 15:
        return "early afternoon"
    elif 15 <= hour < 18:
        return "late afternoon"
    elif 18 <= hour < 21:
        return "early evening"
    else:
        return "late evening"

def get_wind_description(wind_speed):
    """Classify wind speed into low, medium, or high winds."""
    if wind_speed <= 10:
        return "low winds"
    elif 10 < wind_speed <= 20:
        return "medium winds"
    else:
        return "high winds"

def get_weather_forecast():
    # Get the weather forecast for the next 5 days using the 5 Day / 3 Hour Forecast API
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY}&units=imperial"
    
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error fetching weather data: {response.status_code} - {response.text}")
        return None

    data = response.json()
    forecasts = data['list']
    
    # Get today's, tomorrow's, and the day after tomorrow's dates
    today = datetime.now().date()
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    day_after_tomorrow = (datetime.now() + timedelta(days=2)).date()
    
    # Store detailed weather data for the next three days
    weather_report = []
    rain_forecasted_for_tomorrow = False
    
    # Check for weather data
    for forecast in forecasts:
        forecast_time = forecast['dt_txt']
        forecast_date = datetime.strptime(forecast_time, "%Y-%m-%d %H:%M:%S").date()
        forecast_hour = datetime.strptime(forecast_time, "%Y-%m-%d %H:%M:%S").hour
        
        # Only include forecasts for today, tomorrow, and the day after
        if forecast_date in (today, tomorrow, day_after_tomorrow):
            # Extract weather details
            weather_main = forecast['weather'][0]['main']
            description = forecast['weather'][0]['description']
            temperature = round(forecast['main']['temp'])  # Round temperature
            wind_speed = forecast['wind']['speed']
            
            # Check if rain is forecasted for tomorrow
            if forecast_date == tomorrow and 'rain' in weather_main.lower():
                rain_forecasted_for_tomorrow = True
            
            # Store simplified weather information
            weather_report.append({
                'date': forecast_date,
                'time_period': get_time_period(forecast_hour),
                'main': weather_main,
                'description': description,
                'temperature': temperature,
                'wind_speed': wind_speed
            })
    
    return weather_report, rain_forecasted_for_tomorrow

def send_email(subject, body):
    msg = MIMEText(body, "html")
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
    """Create a human-readable weather report with bullet points in HTML."""
    email_body = "<h2>Weather Forecast</h2>\n<ul>\n"
    
    # Group the weather data by day and time period
    grouped_report = {}
    for report in weather_report:
        date_str = report['date'].strftime('%A')
        time_period = report['time_period']
        
        if date_str not in grouped_report:
            grouped_report[date_str] = {}
        
        if time_period not in grouped_report[date_str]:
            grouped_report[date_str][time_period] = report
    
    # Create a two-level list
    for day, time_periods in grouped_report.items():
        email_body += f"<li><strong>{day}</strong>\n<ul>\n"
        for time_period, report in time_periods.items():
            temperature = report['temperature']
            description = report['description']
            wind_speed = report['wind_speed']
            
            # Classify the wind
            wind_description = get_wind_description(wind_speed)
            
            # Bold the rain text if there is rain in the description
            if "rain" in description.lower():
                description = f"<strong>{description}</strong>"
            
            # Add the forecast for each time period
            email_body += (
                f"<li><strong>{time_period.capitalize()}:</strong> "
                f"Temperature: {temperature}°F, {description}, {wind_description}</li>\n"
            )
        email_body += "</ul>\n</li>\n"
    
    email_body += "</ul>\n"
    
    return email_body

def check_rain_forecast():
    # Get the weather report and check if rain is forecasted for tomorrow
    weather_report, rain_forecasted_for_tomorrow = get_weather_forecast()
    
    if weather_report:
        # Only send an email if rain is forecasted for tomorrow
        if rain_forecasted_for_tomorrow:
            email_body = create_weather_report(weather_report)
            subject = "Rain: Boots and Umbrella - Don't Forget"
            send_email(subject, email_body)
        else:
            print("No rain forecasted for tomorrow.")
    else:
        print("No weather data available.")

if __name__ == "__main__":
    check_rain_forecast()
