import os
import json
import logging
import requests
from typing import Tuple, List

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

API_KEY = "579b464db66ec23bdd000001f59af276341944ac508c9a65c45cdaec"
BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

location_prompt = ChatPromptTemplate.from_template("""
Given a city in India, identify its state and district in JSON format.
City: {city}
Respond strictly as:
{{
  "state": "<state>",
  "district": "<district>"
}}
""")

class MandiPriceService:
    def __init__(self) -> None:
        try:
            self.llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model_name="llama3-8b-8192"
            )
            logger.info("✅ Groq LLM initialized for mandi price module")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq LLM: {e}")
            raise

    def get_state_district(self, city: str) -> str:
        prompt = location_prompt.format_messages(city=city)
        response = self.llm.invoke(prompt)
        return response.content

    def parse_state_district(self, llm_output: str) -> Tuple[str, str]:
        try:
            location = json.loads(llm_output)
            return location.get("state", "Unknown"), location.get("district", "Unknown")
        except Exception as e:
            logger.error(f"❌ Error parsing LLM location response: {e}")
            return "Unknown", "Unknown"

    def get_crop_prices(self, crop: str) -> List[dict]:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 100,
            "filters[commodity]": crop
        }

        response = requests.get(BASE_URL, params=params)
        if response.status_code != 200:
            logger.warning(f"❌ Agmarknet API error {response.status_code}")
            return []

        return response.json().get("records", [])

    def prepare_response(self, state: str, district: str, crop: str, records: List[dict]) -> str:
        available_states = {rec["state"] for rec in records}

        # ✅ Primary: District match
        district_records = [r for r in records if r["district"] == district]
        if district_records:
            response = f"✅ Found {crop} prices for {district}, {state}:\n\n"
            for rec in district_records:
                response += (
                    f"📅 {rec['arrival_date']} | 📍 {rec['market']}: "
                    f"₹{rec['min_price']} - ₹{rec['max_price']} per quintal "
                    f"(Modal: ₹{rec['modal_price']} per quintal)\n"
                )
            return response

        # ⚠️ Secondary: Show other districts in the state
        state_district_records = [r for r in records if r["state"] == state]
        if state_district_records:
            response = f"⚠️ No data for {district}, {state}. But found {crop} prices in other districts of {state}:\n\n"
            for d in sorted({r["district"] for r in state_district_records}):
                d_recs = [r for r in state_district_records if r["district"] == d]
                min_price = min(int(r["min_price"]) for r in d_recs)
                max_price = max(int(r["max_price"]) for r in d_recs)
                response += f"➡️ {d}: ₹{min_price} - ₹{max_price} per quintal\n"
            return response

        # ❌ Fallback: Show available states
        response = f"⚠️ No data for {crop} in {state}. But found it in these states:\n\n"
        for s in sorted(available_states):
            s_recs = [r for r in records if r["state"] == s]
            min_price = min(int(r["min_price"]) for r in s_recs)
            max_price = max(int(r["max_price"]) for r in s_recs)
            response += f"➡️ {s}: ₹{min_price} - ₹{max_price} per quintal\n"

        return response

    def list_available_crops(self) -> str:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 100
        }

        response = requests.get(BASE_URL, params=params)
        if response.status_code != 200:
            return "❌ Unable to fetch crop list."

        records = response.json().get("records", [])
        crops = sorted({rec["commodity"] for rec in records})

        if not crops:
            return "⚠️ No crop data available right now."

        return "⚠️ No data found for your crop. Available crops:\n\n" + ", ".join(crops)

    def search_prices(self, city: str, crop: str) -> str:
        logger.info(f"🌾 Mandi search for city: {city}, crop: {crop}")

        try:
            llm_result = self.get_state_district(city)
            state, district = self.parse_state_district(llm_result)

            if state == "Unknown" or district == "Unknown":
                return f"❌ Could not determine state/district for '{city}'."

            records = self.get_crop_prices(crop)

            if not records:
                logger.warning("⚠️ No data found for this crop in the API.")
                return self.list_available_crops()

            return self.prepare_response(state, district, crop, records)

        except Exception as e:
            logger.error(f"❌ Error during mandi price search: {e}")
            return "❌ Internal error while processing mandi prices."
