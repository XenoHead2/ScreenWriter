import os

try:
    from google import genai
except ImportError:
    genai = None

def get_client():
    if not genai:
        return None
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    try:
        return genai.Client(api_key=api_key) if api_key else genai.Client()
    except Exception:
        return None

def analyze_script_context(paragraphs):
    """Helper to extract clean text from the editor and analyze it."""
    if not genai:
        return "Error: Missing library. Please run: pip install google-genai"
    client = get_client()
    if not client:
        return "Error: No API key was provided. Please ensure GEMINI_API_KEY is set in your environment variables."

    # Load custom rules to prevent repeated AI mistakes
    rules_text = ""
    rules_file = "world_rules.txt"
    if os.path.exists(rules_file):
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_content = f.read().strip()
            if rules_content:
                rules_text = f"\nIMPORTANT WORLDBUILDING RULES & CONTEXT TO FOLLOW (Ignore \"errors\" related to these):\n{rules_content}\n"

    # Create numbered text for the AI to reference easily
    numbered_lines = []
    for i, text in enumerate(paragraphs):
        line_text = text.replace('\u200b', '').strip()
        
        # Skip empty lines, page breaks (dashes/equals), and page numbers
        if not line_text or line_text.strip('-=') == "":
            continue
        if line_text.endswith('.') and line_text[:-1].isdigit():
            continue
            
        numbered_lines.append(f"Line#{i+1}: {line_text}")

    if not numbered_lines:
        return "No text found to analyze."

    # Process in chunks to prevent server disconnects and timeouts on massive scripts
    chunk_size = 800
    responses = []
    
    for i in range(0, len(numbered_lines), chunk_size):
        chunk = numbered_lines[i:i+chunk_size]
        numbered_script_text = '\n'.join(chunk)

        prompt = f"""
        You are an expert Hollywood screenplay editor and script consultant. 
        Analyze the following movie script text for stylistic, pacing, and formatting improvements. 
        Do not rewrite the text for me. Instead, provide a structured report detailing:
        
        1. Dialogue & Subtext: Highlight clunky dialogue, on-the-nose exposition, or where subtext could be improved.
        2. Pacing & Action: Highlight action lines that are too novelistic, unfilmable, overly dense, or drag the pacing. (Keep in mind action lines should be brief and visual).
        3. Formatting & Clarity: Pinpoint any awkward scene headings, transitions, passive voice, or incorrect character introductions.
        4. Always make ONE suggestion per line, and reference the line number in your report (e.g., "Line#45: ..."). Do NOT provide multiple suggestions for the same line. If a line has multiple issues, choose the most important one to highlight.

        IMPORTANT: You MUST include the exact line reference for EACH and EVERY suggestion using the exact format "Line#X" (e.g., Line#1, Line#45).
        IMPORTANT: Leave a blank line between each individual suggestion for readability.
        IMPORTANT: Do not include any introductory or concluding fluff (like "Here is an analysis..."). Start directly with the structured report.
        {rules_text}
        Script to analyze:
        {numbered_script_text}
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
            )
            responses.append(response.text)
        except Exception as e:
            responses.append(f"API Error (Lines {i+1} to {i+len(chunk)}): {str(e)}")

    return "\n\n---\n\n".join(responses)

def auto_fix_script(selected_text):
    """Fixes the grammar and flow of a specific selected block of script."""
    if not genai:
        return "Error: Missing library. Please run: pip install google-genai"
    client = get_client()
    if not client:
        return "Error: No API key provided."
        
    prompt = f"Fix the grammar, flow, and formatting of the following movie script text. Preserve the original tone and meaning. Make sure it adheres to professional screenplay standards. Output ONLY the fixed text, with no introductory or concluding text, no quotes around it, and no markdown formatting:\n\n{selected_text}"
    
    try:
        response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error during auto-fix: {str(e)}"

def get_ai_suggestions(selected_text):
    """Generates creative suggestions or rewrites for a selected block of text."""
    if not genai:
        return "Error: Missing library. Please run: pip install google-genai"
    client = get_client()
    if not client:
        return "Error: No API key provided."
        
    prompt = f"You are a professional screenwriter co-writer. Please provide 3 creative alternatives, improvements, or punches-up for the following screenplay text. Keep the suggestions concise, preserve the original intent, and provide only the suggestions without any introductory fluff. Separate each distinct suggestion using exactly '|||' as a delimiter:\n\n{selected_text}"
    
    try:
        response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error during AI suggestion: {str(e)}"