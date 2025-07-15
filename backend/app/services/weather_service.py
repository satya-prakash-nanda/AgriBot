import os
import requests
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
# ✅ Setup logger
logger = logging.getLogger(__name__)

# ✅ Weather API key
weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")

# ✅ Get raw 24-hour forecast from OpenWeatherMap
def get_forecast(city: str):
    logger.info(f"🌦️ Fetching forecast for city: {city}")
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={weather_api_key}&units=metric"
    
    try:
        res = requests.get(url)
        data = res.json()
    except Exception as e:
        logger.error(f"❌ Weather API request failed: {e}")
        return None, "❌ Weather API request failed."

    if data.get("cod") != "200":
        logger.warning(f"❌ Could not fetch forecast for {city}: {data.get('message')}")
        return None, f"❌ Could not fetch forecast for {city}."

    forecast_text = f"📅 Next 24-hour Forecast for {city.title()}:\n"

    # Extract next 8 slots (each 3 hours)
    for entry in data['list'][:8]:
        time = entry['dt_txt']
        desc = entry['weather'][0]['description']
        temp = entry['main']['temp']
        humidity = entry['main']['humidity']
        rain = entry.get('rain', {}).get('3h', 0)

        forecast_text += (
            f"\n🕒 {time}:\n"
            f"→ {desc}, Temp: {temp}°C, Humidity: {humidity}%, Rain (3h): {rain} mm"
        )

    logger.info("✅ Weather forecast data fetched successfully")
    return data, forecast_text


# ✅ Simplify the forecast for farmers using Groq LLM
def simplify_forecast_for_farmer(city: str, forecast_text: str) -> str:
    logger.info("🤖 Simplifying forecast using Groq LLM")

    try:
        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama3-8b-8192"
        )

        prompt = (
        f"You are an agricultural weather advisor helping Indian farmers understand weather forecasts.\n\n"
        f"Here is the forecast for {city}:\n{forecast_text}\n\n"
        f"Summarize this forecast in simple and respectful words that a farmer can easily understand.\n"
        f"Explain how the weather will feel today and tomorrow—whether it will be sunny, rainy, humid, or dry.\n"
    )

        simplified_forecast = llm.invoke(prompt).content
        logger.info("✅ Simplified forecast generated")
        return simplified_forecast

    except Exception as e:
        logger.error(f"❌ Failed to simplify forecast: {e}")
        return "❌ Could not generate simplified forecast."
