"""
AI Research Agent - FINAL FIX VERSION
Forces full essay generation without interruption
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from config import (
    LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE, SYSTEM_PROMPTS,
    QUERY_KEYWORDS, OUTPUT_DIR, LOG_DIR, TASKS_FILE, HISTORY_FILE
)

# ============= Logging Setup =============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ResearchAgent:
    """Main AI agent for research tasks - FIXED VERSION"""
    
    def __init__(self, model: str = LLM_MODEL):
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        logger.info(f"ResearchAgent initialized with model: {model}")
    
    def detect_query_type(self, query: str) -> str:
        """Detect the type of query"""
        query_lower = query.lower()
        
        # Check for essay keywords first (more specific)
        essay_keywords = ["write", "essay", "explain", "describe", "comprehensive", 
                         "detailed", "full", "complete", "article"]
        if any(keyword in query_lower for keyword in essay_keywords):
            return "essay"
        
        # Check other types
        for query_type, keywords in QUERY_KEYWORDS.items():
            if query_type != "essay":  # Skip essay, already checked
                if any(keyword in query_lower for keyword in keywords):
                    return query_type
        
        return "research"
    
    def get_system_prompt(self, query_type: str) -> str:
        """Get system prompt based on query type"""
        return SYSTEM_PROMPTS.get(query_type, SYSTEM_PROMPTS.get("research", ""))
    
    def process_single_query(self, query: str) -> Dict[str, Any]:
        """Process a single research query with DIRECT generation"""
        logger.info(f"Processing query: {query}")
        
        try:
            # Detect query type
            query_type = self.detect_query_type(query)
            max_tokens = LLM_MAX_TOKENS.get(query_type, 8000)
            
            logger.info(f"Query type: {query_type}, Max tokens: {max_tokens}")
            
            # Get system prompt
            system_prompt = self.get_system_prompt(query_type)
            
            # Create LLM - NO TOOLS, just direct generation
            llm = ChatAnthropic(
                model=self.model,
                max_tokens=max_tokens,
                temperature=LLM_TEMPERATURE
            )
            
            # Use direct message API without tools for clean generation
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            logger.info(f"Invoking LLM with {max_tokens} tokens...")
            
            # Get response directly
            response = llm.invoke(messages)
            
            # Extract text from response
            output_text = self._extract_text_from_response(response)
            
            if not output_text:
                logger.warning("No output text extracted")
                output_text = "Unable to generate response"
            
            logger.info(f"Response generated: {len(output_text)} characters")
            
            result = {
                'query': query,
                'query_type': query_type,
                'response': output_text,
                'tools_used': [],
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                'query': query,
                'query_type': 'unknown',
                'response': None,
                'tools_used': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'status': 'failed'
            }
    
    def _extract_text_from_response(self, response) -> str:
        """Extract text from response"""
        try:
            # Try content attribute
            if hasattr(response, 'content'):
                content = response.content
                
                # Handle list content
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                        elif isinstance(item, str) and item.strip():
                            text_parts.append(item)
                    return " ".join(text_parts).strip()
                else:
                    return str(content).strip()
            
            # Try text attribute
            if hasattr(response, 'text'):
                return response.text.strip()
            
            # Last resort
            return str(response).strip()
        
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ""
    
    def process_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Process multiple queries in batch"""
        logger.info(f"Processing batch of {len(queries)} queries")
        
        results = []
        for i, query in enumerate(queries, 1):
            logger.info(f"[{i}/{len(queries)}] Processing: {query[:50]}")
            result = self.process_single_query(query)
            results.append(result)
        
        # Save results
        try:
            history_file = HISTORY_FILE
            history = []
            
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            history.extend(results)
            
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.info(f"Batch results saved: {history_file}")
        except Exception as e:
            logger.error(f"Error saving batch results: {str(e)}")
        
        return results
