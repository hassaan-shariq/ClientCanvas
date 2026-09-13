from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from groq import Groq
import os
from dotenv import load_dotenv
from database import (
    init_db, add_business, get_all_businesses,
    get_businesses_by_status, update_business_status,
    delete_business, add_contact, get_contacts,
    add_interaction, get_interactions, get_stats
)

load_dotenv()

app = FastAPI(title="ClientCanvas CRM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-20b"

# ===== MODELS =====
class BusinessInput(BaseModel):
    name: str
    type: str
    city: Optional[str] = ""
    website: Optional[str] = ""
    instagram: Optional[str] = ""

class StatusUpdate(BaseModel):
    status: str

class ContactInput(BaseModel):
    name: str
    phone: Optional[str] = ""
    role: Optional[str] = ""

class InteractionInput(BaseModel):
    type: str
    note: str

class PitchRequest(BaseModel):
    business_name: str
    business_type: str
    city: str
    specific_problem: Optional[str] = ""

class FollowUpRequest(BaseModel):
    business_id: int
    last_interaction: str
    days_since_contact: int

class SocialMediaRequest(BaseModel):
    business_name: str
    business_type: str
    target_audience: str
    goal: Optional[str] = "grow followers and get clients"

# ===== HELPERS =====
def ai(prompt: str, max_tokens: int = 600) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant.

Language rule:
- Detect the main language of the user's supplied details and request.
- If the input is English, reply entirely in English.
- If the input is Urdu, including Urdu script or Roman Urdu, reply in natural Roman Urdu.
- Never use Urdu script in the response; use Roman Urdu instead.
- If the input is mixed, use the predominant language.

Formatting rule:
- Never use markdown formatting.
- No asterisks, bold text, tables, or bullet symbols.
- Use plain text only.
- Use numbers for lists and plain dashes for separation."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_completion_tokens=max_tokens,
            temperature=0.5,
            reasoning_effort="low",
            include_reasoning=False
        )

        return (response.choices[0].message.content or "").strip()

    except Exception as e:
        return f"AI Error: {str(e)}"

# ===== BUSINESS ENDPOINTS =====
@app.get("/")
def home():
    return {"message": "ClientCanvas API running"}

@app.post("/businesses")
def create_business(data: BusinessInput):
    business_id = add_business(
        data.name, data.type,
        data.city, data.website, data.instagram
    )
    return {"message": "Business added", "id": business_id}

@app.get("/businesses")
def list_businesses(status: Optional[str] = None):
    if status:
        return get_businesses_by_status(status)
    return get_all_businesses()

@app.put("/businesses/{business_id}/status")
def update_status(business_id: int, data: StatusUpdate):
    update_business_status(business_id, data.status)
    return {"message": "Status updated"}

@app.delete("/businesses/{business_id}")
def remove_business(business_id: int):
    delete_business(business_id)
    return {"message": "Business deleted"}

# ===== CONTACT ENDPOINTS =====
@app.post("/businesses/{business_id}/contacts")
def create_contact(business_id: int, data: ContactInput):
    add_contact(business_id, data.name, data.phone, data.role)
    return {"message": "Contact added"}

@app.get("/businesses/{business_id}/contacts")
def list_contacts(business_id: int):
    return get_contacts(business_id)

# ===== INTERACTION ENDPOINTS =====
@app.post("/businesses/{business_id}/interactions")
def create_interaction(business_id: int, data: InteractionInput):
    add_interaction(business_id, data.type, data.note)
    return {"message": "Interaction logged"}

@app.get("/businesses/{business_id}/interactions")
def list_interactions(business_id: int):
    return get_interactions(business_id)

# ===== STATS =====
@app.get("/stats")
def stats():
    return get_stats()

# ===== AI ENDPOINTS =====
@app.post("/ai/pitch")
def generate_pitch(data: PitchRequest):
    prompt = f"""Write a short WhatsApp outreach message for a freelance AI developer targeting this business:

Business Name: {data.business_name}
Business Type: {data.business_type}
City: {data.city}
Specific Problem: {data.specific_problem}

Rules:
- Maximum 5 lines
- Offer a free demo
- Sound friendly and human
- End with one question
- No greetings like Assalam o Alaikum needed, start directly"""

    result = ai(prompt, 250)
    return {"pitch": result}


@app.post("/ai/followup")
def suggest_followup(data: FollowUpRequest):
    interactions = get_interactions(data.business_id)
    history = "\n".join([
        f"- {i['type']}: {i['note']}"
        for i in interactions[-5:]
    ]) if interactions else "No previous interactions recorded."

    prompt = f"""A freelance AI developer needs a follow-up message for a business lead.

Last interaction: {data.last_interaction}
Days since contact: {data.days_since_contact}
Previous history:
{history}

Provide:
1. Exact follow-up message in the detected input language
2. Best time to send it
3. Why this approach will work

Keep it practical and short."""

    result = ai(prompt, 300)
    return {"suggestion": result}


@app.get("/ai/daily-plan")
def daily_action_plan():
    businesses = get_all_businesses()

    if not businesses:
        return {
            "plan": """No leads in CRM yet. Here is your action plan:

1. Add your first lead using the Add Lead button
2. Send 10 outreach messages to event companies on Instagram
3. Use the Pitch Generator to create personalized messages
4. Call 3 businesses you already messaged

Start by adding warm leads like Multan Events, Eventxa, WD Events."""
        }

    summary = "\n".join([
        f"- {b['name']} in {b.get('city','Pakistan')} "
        f"({b['type']}): Status is {b['status']}"
        for b in businesses[:10]
    ])

    prompt = f"""You are a sales manager. A freelance AI developer has these leads:

{summary}

Create a simple daily action plan:
1. Top 3 leads to focus on today and why
2. One specific action for each lead
3. One motivating sentence

Use plain text only. No formatting symbols."""

    result = ai(prompt, 500)
    return {"plan": result}


@app.get("/ai/analyze/{business_id}")
def analyze_lead(business_id: int):
    try:
        interactions = get_interactions(business_id)
        count = len(interactions)

        history = "\n".join([
            f"- {i['type']}: {i['note']}"
            for i in interactions
        ]) if interactions else "No interactions yet."

        prompt = f"""Analyze this sales lead:

Total interactions: {count}
History:
{history}

Provide:
1. Conversion probability as a percentage
2. Main obstacle to closing this deal
3. Best next action to take
4. One key insight

Be direct and specific. Plain text only."""

        result = ai(prompt, 300)
        return {
            "analysis": result,
            "interaction_count": count
        }
    except Exception as e:
        return {"analysis": f"Error: {str(e)}", "interaction_count": 0}


@app.post("/ai/social-plan")
def social_media_plan(data: SocialMediaRequest):
    prompt = f"""Create a 7-day social media content plan.

Business: {data.business_name}
Type: {data.business_type}
Target Audience: {data.target_audience}
Goal: {data.goal}

For each day write:
Day number, Platform, Content type, Caption ready to post, Best time, 5 hashtags

Focus on Pakistani market. Write in plain text. No tables or markdown."""

    result = ai(prompt, 300)
    return {"social_plan": result}