from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from tools import search_tool, wiki_tool, save_to_txt

load_dotenv()

class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]

# Using Claude Opus 4.1 from Anthropic
llm = ChatAnthropic(
    model="claude-opus-4-1-20250805",
    max_tokens=4096  # Increased to get complete responses
)
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

# Tools list
tools_list = [search_tool, wiki_tool, save_to_txt]

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools_list)

# Main execution - get query from user
query = input("What can I help you research? ")

# Increase tokens for essays
if "essay" in query.lower() or "write" in query.lower():
    llm = ChatAnthropic(
        model="claude-opus-4-1-20250805",
        max_tokens=16000  # Maximum tokens for essays
    )
    llm_with_tools = llm.bind_tools(tools_list)

# Detect query type for better prompting
query_lower = query.lower()
is_essay = any(word in query_lower for word in ["essay", "explain", "describe", "discuss", "write about", "tell me about"])

if is_essay:
    system_instruction = """
    You are an expert essay writer. Write an EXTREMELY LONG, COMPREHENSIVE, AND DETAILED essay.
    
    CRITICAL - WORD COUNT REQUIREMENT: 
    MINIMUM 8000-10000 WORDS (This is a requirement, not optional)
    
    ESSAY STRUCTURE REQUIREMENTS:
    - Introduction: 4-5 paragraphs (800+ words) with comprehensive thesis
    - Body Section 1: 4-5 paragraphs (800+ words) on first major point
    - Body Section 2: 4-5 paragraphs (800+ words) on second major point
    - Body Section 3: 4-5 paragraphs (800+ words) on third major point
    - Body Section 4: 4-5 paragraphs (800+ words) on fourth major point (optional but recommended)
    - Analysis Section: 4-5 paragraphs (800+ words) with critical analysis
    - Conclusion: 4-5 paragraphs (800+ words) with comprehensive summary
    
    CONTENT REQUIREMENTS:
    - EVERY paragraph must be 200-300 words minimum
    - Include specific examples, case studies, statistics, and evidence
    - Add direct quotes and citations from reliable sources
    - Explore multiple perspectives and viewpoints
    - Use academic, professional tone throughout
    - Include transitions between all sections
    - Add sub-arguments and counter-arguments
    - Provide detailed analysis and synthesis
    
    CRITICAL INSTRUCTIONS:
    - DO NOT ABBREVIATE or SUMMARIZE at any point
    - Generate the COMPLETE FULL-LENGTH essay
    - Use ALL available space and tokens
    - Make sure to cover all aspects comprehensively
    - This must be a thorough, academic-quality essay
    - Each point should be explained in extreme detail
    
    After gathering information, wrap your final response in this format and provide no other text\n{format_instructions}
    """
else:
    system_instruction = """
    You are a research assistant that will help generate a comprehensive research paper.
    Answer the user query thoroughly and use necessary tools to gather detailed information. 
    Provide a complete, well-researched response with multiple sources and insights.
    After gathering information, wrap your final response in this format and provide no other text\n{format_instructions}
    """

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            system_instruction,
        ),
        ("human", "{query}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# Create chain
chain = prompt | llm_with_tools

try:
    print("\n🔍 Researching your query with Claude...")
    response = chain.invoke({"query": query})
    
    # Extract text content from response
    if hasattr(response, 'content'):
        output_text = response.content
    else:
        output_text = str(response)
    
    # Handle tool calls if any
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"\n📚 Claude is using {len(response.tool_calls)} tool(s)...")
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_input = tool_call.get('args', {})
            
            # Find and execute the tool
            for t in tools_list:
                if t.name == tool_name:
                    try:
                        result = t.invoke(tool_input)
                        print(f"   ✓ {tool_name}:")
                        print(f"      {str(result)}")  # Show complete result
                    except Exception as e:
                        print(f"   ✗ {tool_name}: Error")
                        print(f"      {str(e)}")  # Show complete error
    
    # Try to parse as structured response
    try:
        structured_response = parser.parse(output_text)
        print("\n=== Research Results ===")
        print(structured_response)
    except Exception as parse_error:
        print(f"\n=== Raw Response ===")
        print(output_text)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
