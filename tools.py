from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool
from datetime import datetime


def clean_and_filter_result(text: str, max_length: int = 2000) -> str:
    """Clean and filter tool results to remove irrelevant/mixed content"""
    if not text:
        return "No relevant information found."
    
    result = str(text).strip()
    
    # Remove non-English noise and mixed language content
    # Split by double newlines and take coherent sections
    sections = result.split('\n\n')
    
    cleaned_sections = []
    for section in sections:
        section = section.strip()
        # Skip very short or mostly URL sections
        if len(section) > 50 and not section.startswith('http'):
            # Check if section has too many non-ASCII characters (likely mixed languages)
            non_ascii_ratio = sum(1 for c in section if ord(c) > 127) / len(section) if section else 0
            if non_ascii_ratio < 0.3:  # Allow some non-ASCII but not too much
                cleaned_sections.append(section)
    
    # Take the first 1-2 coherent sections
    if cleaned_sections:
        result = '\n\n'.join(cleaned_sections[:2])
    else:
        # Fallback: take first part
        result = sections[0] if sections else result
    
    # Limit total length
    if len(result) > max_length:
        # Try to cut at sentence boundary
        truncated = result[:max_length]
        last_period = truncated.rfind('.')
        if last_period > max_length - 500:  # If period is within reasonable range
            result = truncated[:last_period + 1]
        else:
            result = truncated + "..."
    
    return result.strip()


@tool
def save_to_txt(data: str) -> str:
    """Saves research data to a text file with timestamp. Use this to save the final research output."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Research Output ---\nTimestamp: {timestamp}\n\n{data}\n\n"
    
    try:
        with open("research_output.txt", "a", encoding="utf-8") as f:
            f.write(formatted_text)
        return f"Data successfully saved to research_output.txt"
    except Exception as e:
        return f"Error saving file: {str(e)}"


@tool
def search(query: str) -> str:
    """Search the web for current information using DuckDuckGo. Returns cleaned, relevant results."""
    try:
        search_engine = DuckDuckGoSearchRun()
        result = search_engine.run(query)
        # Clean and filter the result to remove noise
        cleaned = clean_and_filter_result(result, max_length=1500)
        return cleaned
    except Exception as e:
        return f"Error during search: {str(e)}"


@tool  
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for information. Returns cleaned, relevant results only."""
    try:
        api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=1000)
        wiki = WikipediaQueryRun(api_wrapper=api_wrapper)
        result = wiki.run(query)
        # Clean and filter the result
        cleaned = clean_and_filter_result(result, max_length=1500)
        return cleaned
    except Exception as e:
        return f"Error: {str(e)}"


# Create tools for use
search_tool = search
wiki_tool = wikipedia_search
tools_list = [search_tool, wiki_tool, save_to_txt]
