# ==============================================================================
# File: processing/ai_analyzer.py
# ==============================================================================

import os
import json
from typing import List, Dict, Optional, Tuple

# --- LLM Client Configuration ---
# This section dynamically configures which LLM service to use.
# It prioritizes Groq if an API key is provided, otherwise falls back to local Ollama.

# Attempt to import client libraries
try:
    from groq import Groq
    groq_available = True
except ImportError:
    groq_available = False

try:
    import ollama
    ollama_available = True
except ImportError:
    ollama_available = False

# Determine which service to use
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_GROQ = groq_available and GROQ_API_KEY

llm_client = None
LLM_MODEL = None

if USE_GROQ:
    print("AI ANALYZER: Configuring to use Groq Cloud API.")
    llm_client = Groq(api_key=GROQ_API_KEY)
    LLM_MODEL = "llama3-8b-8192"  # Groq's Llama 3 8B model
else:
    if ollama_available:
        print("AI ANALYZER: Configuring to use local Ollama.")
        try:
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            llm_client = ollama.Client(host=ollama_host)
            llm_client.list()  # Verify connection by listing local models
            LLM_MODEL = "tinyllama" # Change if you use a different local model
            print(f"AI ANALYZER: Connection to Ollama at {ollama_host} successful.")
        except Exception as e:
            print(f"FATAL: Could not connect to Ollama at {ollama_host}. Please ensure Ollama is running. Error: {e}")
            llm_client = None # Explicitly set to None on failure
    else:
        print("FATAL: No LLM clients could be configured. Neither Groq nor Ollama is available.")


# --- Prompt Engineering ---

# This prompt is highly structured to force the LLM into returning a clean JSON object.
# Note: We've removed contact_info and sentiment from the JSON structure, as we handle them separately.
ANALYSIS_SYSTEM_PROMPT = """
You are an expert business analyst AI. Your task is to analyze the content from a company's homepage and extract key business information.
Respond ONLY with a single, valid JSON object. Do not include any text, explanations, or markdown formatting before or after the JSON.
The JSON object must strictly follow this structure:
{
  "industry": "A specific industry category (e.g., 'Financial Technology', 'E-commerce', 'Healthcare SaaS') or 'N/A' if not found.",
  "company_size": "An estimated size (e.g., 'Startup (1-10 employees)', 'Medium (50-200 employees)', 'Large Enterprise (>1000 employees)') or 'N/A' if not found.",
  "location": "The primary headquarters or location (e.g., 'San Francisco, CA, USA') or 'N/A' if not found.",
  "core_products_services": ["A list of the main products or services offered."],
  "unique_selling_proposition": "A concise, one-sentence summary of what makes the company unique.",
  "target_audience": "A description of the primary customer demographic (e.g., 'Small to Medium Businesses (SMBs)', 'Individual Consumers', 'Large Enterprises')."
}
If information for a field is not available in the provided text, use "N/A" for strings and an empty list [] for arrays.
"""

def _generate_llm_response(messages: List[Dict[str, str]], json_mode: bool = False) -> str:
    """A unified, robust internal function to call the configured LLM."""
    if not llm_client:
        raise Exception("LLM client is not initialized. Please check your configuration and ensure the service (Ollama or Groq) is running.")

    try:
        if USE_GROQ:
            response = llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=2048,
                # Only use JSON mode if explicitly requested
                response_format={"type": "json_object"} if json_mode else None
            )
            return response.choices[0].message.content
        else: # Using Ollama
            response = llm_client.chat(
                model=LLM_MODEL,
                messages=messages,
                # Only use JSON mode if explicitly requested
                format='json' if json_mode else ''
            )
            return response['message']['content']
    except Exception as e:
        print(f"LLM API call failed. Error: {e}")
        raise


async def analyze_content_with_llm(scraped_data: Dict, custom_questions: Optional[List[str]]) -> Dict:
    """Analyzes website content to extract core business details and answer specific questions."""
    print(f"Analyzing content for {scraped_data.get('url', 'N/A')}")
    
    # Consolidate website text for the LLM context
    context_text = f"Title: {scraped_data['metadata']['title']}\n" \
                   f"Meta Description: {scraped_data['metadata']['description']}\n\n" \
                   f"--- Website Content ---\n{scraped_data['main_content']}"

    # --- 1. Perform structured JSON analysis for core company info ---
    analysis_messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": context_text}
    ]
    
    company_info = {}
    try:
        raw_response = _generate_llm_response(analysis_messages, json_mode=True)
        # Add a fallback to handle cases where the LLM might ignore JSON mode
        # and wrap its response in markdown ```json ... ```
        if raw_response.strip().startswith("```json"):
            raw_response = raw_response.strip()[7:-3]
            
        company_info = json.loads(raw_response)

    except json.JSONDecodeError as e:
        print(f"LLM JSON DECODE ERROR: {e}. Raw response: {raw_response}")
        raise Exception("The AI model returned data in an invalid format. Could not parse company info.")
    except Exception as e:
        print(f"LLM ANALYSIS ERROR: {e}")
        raise

    # --- 2. Manually construct the contact_info from scraped data ---
    # This is more reliable than asking the LLM for it.
    company_info['contact_info'] = {
        "email": scraped_data['contact_info']['emails'][0] if scraped_data['contact_info']['emails'] else None,
        "phone": scraped_data['contact_info']['phones'][0] if scraped_data['contact_info']['phones'] else None,
        "social_media": scraped_data['contact_info']['social_links']
    }
    
    # --- 3. Answer custom questions if any are provided ---
    extracted_answers = []
    if custom_questions:
        print(f"Answering {len(custom_questions)} custom questions...")
        qa_system_prompt = "You are a helpful question-answering assistant. Use the provided context to answer the user's question concisely. If the answer is not in the context, state that the information is not available on the homepage."
        
        for question in custom_questions:
            qa_messages = [
                {"role": "system", "content": qa_system_prompt},
               # --- AFTER ---
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}
            ]
            try:
                answer = _generate_llm_response(qa_messages, json_mode=False)
                extracted_answers.append({"question": question, "answer": answer})
            except Exception as e:
                extracted_answers.append({"question": question, "answer": f"Error generating answer: {e}"})

    return {"company_info": company_info, "extracted_answers": extracted_answers}


async def answer_follow_up_question(scraped_data: Dict, query: str, history: List[Dict]) -> Tuple[str, List[str]]:
    """Answers a follow-up question using website content and conversation history."""
    print(f"Handling follow-up query for {scraped_data.get('url', 'N/A')}")
    
    system_prompt = """You are a helpful and conversational AI agent. Your purpose is to answer questions about a company based on the content of their website.
    Use the 'Website Content Context' and the 'Conversation History' to provide a comprehensive answer to the 'User's Latest Query'.
    Be conversational and clear. If the information is not present in the provided context, state that you cannot find the answer on the homepage."""

    context_text = f"Title: {scraped_data['metadata']['title']}\n" \
                   f"Meta Description: {scraped_data['metadata']['description']}\n\n" \
                   f"--- Website Content ---\n{scraped_data['main_content']}"

    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "system", "content": f"Website Content Context:\n{context_text}"})

    # Add conversation history, if any
    if history:
        history_text = "\n".join([f"User: {turn.get('user_query', '')}\nAI: {turn.get('agent_response', '')}" for turn in history])
        messages.append({"role": "system", "content": f"Conversation History:\n{history_text}"})

    messages.append({"role": "user", "content": f"User's Latest Query: {query}"})

    try:
        response = _generate_llm_response(messages, json_mode=False)
        # For this demo, we'll return a static context source. A real implementation might be more dynamic.
        context_sources = ["Homepage Text Content"]
        return response, context_sources
    except Exception as e:
        raise Exception(f"An error occurred during conversational LLM call: {e}")