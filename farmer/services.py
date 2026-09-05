import os
import json
import joblib
from groq import Groq
from dotenv import load_dotenv


class CattleAIService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv()

        self.model = joblib.load(os.path.join(base_dir, 'cattle_diseases_model.pkl'))
        self.model_features = joblib.load(os.path.join(base_dir, 'model_features.pkl'))

        self.valid_symptoms = [
            f for f in self.model_features
            if f not in ['Age', 'Temperature'] and not f.startswith('Animal')
        ]

        # API key + model are read from the environment so they can be swapped
        # without touching code (e.g. point GROQ_MODEL at a fine-tuned model).
        self.groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
        self.model_name = os.environ.get('GROQ_MODEL', 'llama-3.1-8b-instant')

    def extract_symptoms_with_groq(self, farmer_text):
        system_prompt = f"""
            You are a veterinary assistant. Analyse the text and extract symptoms matching exactly this list:
            {self.valid_symptoms}
            Respond with a JSON object: {{"symptoms": ["symptom_name"]}}
        """
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Farmer text: \"{farmer_text}\""}
                ],
                model=self.model_name,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content.strip()
            result_json = json.loads(response_text)
            return result_json.get('symptoms', [])
        except Exception as e:
            print(f"Groq Extraction Error: {e}")
            return []

    def get_treatment_recommendation(self, disease, animal_type):
        system_prompt = """
            You are a veterinary expert. Provide clear, concise and professional treatment recommendations
            under 120 words using short bullet points. Include a vet disclaimer.
        """
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Treatment recommendation for a {animal_type} with {disease}"}
                ],
                model=self.model_name,
                temperature=0.3,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq Treatment Error: {e}")
            return "Treatment temporarily unavailable"

    def predict(self, animal_type, age, temp, description):
        extracted_symptoms = self.extract_symptoms_with_groq(description)

        input_data = {feature: 0 for feature in self.model_features}
        input_data['Age'] = age
        input_data['Temperature'] = temp

        animal_key = f"Animal_{str(animal_type).strip().lower()}"
        if animal_key in input_data:
            input_data[animal_key] = 1

        for symptom in extracted_symptoms:
            if symptom in input_data:
                input_data[symptom] = 1

        final_input_vector = [input_data[f] for f in self.model_features]
        prediction = self.model.predict([final_input_vector])
        predicted_disease = prediction[0]

        treatment_plan = self.get_treatment_recommendation(predicted_disease, animal_type)

        return {
            "status": "success",
            "extracted_symptoms_by_ai": extracted_symptoms,
            "predicted_disease": predicted_disease,
            "treatment_recommendation": treatment_plan,
        }
