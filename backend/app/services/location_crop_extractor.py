import os
import json
import logging
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

logger = logging.getLogger(__name__)


class EntityExtractor:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=os.environ["GROQ_API_KEY"],
            model_name="llama3-8b-8192"
        )

    def extract_weather_city(self, query: str) -> str:
        prompt = (
            "You are an assistant that extracts the **Indian city name only** from a user's query about weather.\n"
            "If no Indian city is found, reply with \"unknown\".\n"
            "Reply with the city name only, no explanation.\n"
            f"User query: \"{query}\"\n"
            "City name:"
        )
        response = self.llm([HumanMessage(content=prompt)])
        city = response.content.strip()
        if city.lower() in ["", "none", "unknown"]:
            logger.warning(f"❌ Could not extract city from query: {query}")
        return city

    def extract_mandi_entities(self, query: str) -> dict:
        prompt = (
            "You are an assistant that extracts the **crop name (singular form)** and the **location (Indian city or district)** "
            "from a user's mandi price query.\n"
            "Crop names should be in singular form. For example, return \"tomato\" instead of \"tomatoes\".\n"
            "If either the crop or location is missing, leave it blank in the JSON.\n"
            "Reply only in this strict JSON format:\n"
            "{ \"crop\": \"<crop_name>\", \"location\": \"<location_name>\" }\n\n"
            f"User query: \"{query}\"\n"
            "JSON result:"
        )
        response = self.llm([HumanMessage(content=prompt)])

        try:
            result = json.loads(response.content)
            crop = result.get("crop", "").strip().lower()
            location = result.get("location", "").strip()
            return {"crop": crop, "location": location}
        except Exception as e:
            logger.error(f"Error parsing mandi entity extraction response: {e} | Response: {response.content}")
            return {"crop": "", "location": ""}
