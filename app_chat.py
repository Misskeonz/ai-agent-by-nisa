"""
Advanced Chat Interface with Conversation Memory
Full conversational research like Claude.ai with context awareness
"""

import json
import logging
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from io import StringIO

import streamlit as st
from dotenv import load_dotenv

from agent import ResearchAgent
from config import PAGE_LAYOUT, INITIAL_SIDEBAR_STATE, OUTPUT_DIR, LOG_DIR

# ============= Knowledge Base System =============
class KnowledgeBase:
    """Manage custom knowledge and documents"""
    
    def __init__(self, storage_dir: str = "./knowledge"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.kb_file = self.storage_dir / "knowledge_base.json"
        self.load_knowledge()
    
    def load_knowledge(self):
        """Load knowledge base from file"""
        if self.kb_file.exists():
            with open(self.kb_file, 'r') as f:
                self.knowledge = json.load(f)
        else:
            self.knowledge = {"custom": [], "documents": [], "facts": []}
    
    def save_knowledge(self):
        """Save knowledge base to file"""
        with open(self.kb_file, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
    
    def add_custom_knowledge(self, title: str, content: str, category: str = "general"):
        """Add custom knowledge"""
        item = {
            "id": len(self.knowledge["custom"]) + 1,
            "title": title,
            "content": content,
            "category": category,
            "added_at": datetime.now().isoformat()
        }
        self.knowledge["custom"].append(item)
        self.save_knowledge()
        return item["id"]
    
    def add_document(self, filename: str, content: str):
        """Add document to knowledge base"""
        item = {
            "id": len(self.knowledge["documents"]) + 1,
            "filename": filename,
            "content": content[:5000],
            "added_at": datetime.now().isoformat()
        }
        self.knowledge["documents"].append(item)
        self.save_knowledge()
        return item["id"]
    
    def add_fact(self, fact: str, source: str = ""):
        """Add a fact"""
        item = {
            "id": len(self.knowledge["facts"]) + 1,
            "fact": fact,
            "source": source,
            "added_at": datetime.now().isoformat()
        }
        self.knowledge["facts"].append(item)
        self.save_knowledge()
        return item["id"]
    
    def search_knowledge(self, query: str):
        """Search all knowledge"""
        query_lower = query.lower()
        results = []
        
        for item in self.knowledge["custom"]:
            if query_lower in item["content"].lower() or query_lower in item["title"].lower():
                results.append({"type": "custom", "data": item})
        
        for item in self.knowledge["documents"]:
            if query_lower in item["content"].lower() or query_lower in item["filename"].lower():
                results.append({"type": "document", "data": item})
        
        for item in self.knowledge["facts"]:
            if query_lower in item["fact"].lower():
                results.append({"type": "fact", "data": item})
        
        return results
    
    def get_system_context(self) -> str:
        """Get knowledge as system context for LLM"""
        context = "AVAILABLE KNOWLEDGE:\n\n"
        
        if self.knowledge["custom"]:
            context += "CUSTOM KNOWLEDGE:\n"
            for item in self.knowledge["custom"]:
                context += f"- [{item['category']}] {item['title']}: {item['content']}\n"
        
        if self.knowledge["documents"]:
            context += "\nDOCUMENTS:\n"
            for item in self.knowledge["documents"]:
                context += f"- {item['filename']}: {item['content'][:200]}...\n"
        
        if self.knowledge["facts"]:
            context += "\nFACTS:\n"
            for item in self.knowledge["facts"]:
                context += f"- {item['fact']}"
                if item['source']:
                    context += f" (Source: {item['source']})"
                context += "\n"
        
        return context
    
    def get_stats(self):
        """Get knowledge base statistics"""
        return {
            "custom": len(self.knowledge["custom"]),
            "documents": len(self.knowledge["documents"]),
            "facts": len(self.knowledge["facts"]),
            "total": len(self.knowledge["custom"]) + len(self.knowledge["documents"]) + len(self.knowledge["facts"])
        }

load_dotenv()

# ============= Page Configuration =============
st.set_page_config(
    page_title="💬 Research ChatBox Pro",
    page_icon="💬",
    layout=PAGE_LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE
)

# ============= Custom CSS =============
st.markdown("""
    <style>
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .user-message {
        background-color: #2196f3;
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        max-width: 80%;
        margin-left: auto;
        margin-right: 0;
        word-wrap: break-word;
    }
    .assistant-message {
        background-color: #f5f5f5;
        color: black;
        padding: 1rem;
        border-radius: 1rem;
        max-width: 100%;
        margin-left: 0;
        margin-right: auto;
        border-left: 4px solid #4caf50;
    }
    .message-time {
        font-size: 0.8em;
        color: #999;
        margin-top: 0.5rem;
    }
    .response-length {
        font-size: 0.9em;
        color: #666;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ============= Logging =============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "chat_advanced.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============= Table Extraction Function =============
def extract_tables_from_text(text: str) -> list:
    """Extract markdown tables from text"""
    tables = []
    
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if line looks like a table header
        if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            try:
                # Collect table lines
                table_lines = [line]
                i += 1
                table_lines.append(lines[i])  # separator line
                i += 1
                
                # Collect data rows
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                
                # Parse table
                headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
                rows = []
                
                for row_line in table_lines[2:]:
                    cells = [c.strip() for c in row_line.split('|')[1:-1]]
                    if len(cells) == len(headers) and any(cells):
                        rows.append(dict(zip(headers, cells)))
                
                if rows:
                    df = pd.DataFrame(rows)
                    tables.append(df)
                continue
            except:
                i += 1
                continue
        i += 1
    
    return tables

# ============= Session State =============
if "agent" not in st.session_state:
    st.session_state.agent = ResearchAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "tables" not in st.session_state:
    st.session_state.tables = []

if "kb" not in st.session_state:
    st.session_state.kb = KnowledgeBase()

agent = st.session_state.agent
kb = st.session_state.kb

# ============= Header =============
st.title("💡 Research ChatBox with Knowledge Base")
st.markdown("""
**Chat + Add Knowledge + Upload Documents**
- 💬 Full chat history
- 💡 Add custom knowledge
- 📄 Upload documents
- 📌 Quick facts
- 📊 Generate tables
- 💾 Export everything
""")

# ============= Sidebar =============
with st.sidebar:
    st.header("⚙️ Chat Settings")
    
    # ============= Knowledge Management Section =============
    st.subheader("💡 Knowledge Base")
    
    kb_col1, kb_col2, kb_col3 = st.columns(3)
    with kb_col1:
        if st.button("➕ Add", use_container_width=True):
            st.session_state.kb_mode = "add"
    with kb_col2:
        if st.button("📊 Stats", use_container_width=True):
            st.session_state.kb_mode = "stats"
    with kb_col3:
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.kb_mode = "search"
    
    if "kb_mode" not in st.session_state:
        st.session_state.kb_mode = "add"
    
    # Add knowledge
    if st.session_state.kb_mode == "add":
        with st.expander("Custom Knowledge", expanded=True):
            kb_title = st.text_input("Title", placeholder="e.g., Company Info", key="kb_title")
            kb_content = st.text_area("Content", placeholder="Your knowledge...", height=100, key="kb_content")
            kb_category = st.selectbox("Category", ["general", "company", "product", "technical", "other"], key="kb_cat")
            
            if st.button("💾 Save Knowledge", use_container_width=True):
                if kb_title and kb_content:
                    kb.add_custom_knowledge(kb_title, kb_content, kb_category)
                    st.success("✅ Knowledge added!")
                else:
                    st.error("Fill all fields")
        
        with st.expander("Quick Facts", expanded=False):
            fact_text = st.text_input("Fact", placeholder="e.g., Malaysia has 13 states", key="fact")
            fact_source = st.text_input("Source", placeholder="Optional", key="source")
            
            if st.button("💾 Save Fact", use_container_width=True):
                if fact_text:
                    kb.add_fact(fact_text, fact_source)
                    st.success("✅ Fact added!")
                else:
                    st.error("Enter a fact")
        
        with st.expander("Upload Document", expanded=False):
            uploaded_file = st.file_uploader("Choose file", type=['txt', 'md', 'pdf'], key="doc_upload")
            
            if uploaded_file is not None and st.button("📤 Upload", use_container_width=True):
                try:
                    content = uploaded_file.read().decode('utf-8')
                    kb.add_document(uploaded_file.name, content)
                    st.success("✅ Document added!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Show statistics
    elif st.session_state.kb_mode == "stats":
        stats = kb.get_stats()
        st.write("**Knowledge Statistics:**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Custom", stats["custom"])
            st.metric("Facts", stats["facts"])
        with col2:
            st.metric("Documents", stats["documents"])
            st.metric("Total", stats["total"])
    
    # Search knowledge
    else:
        search_query = st.text_input("🔍 Search", placeholder="Search knowledge", key="search_kb")
        
        if search_query:
            results = kb.search_knowledge(search_query)
            if results:
                st.write(f"**Found {len(results)} results:**")
                for result in results[:5]:
                    title = result['data'].get('title', result['data'].get('filename', result['data'].get('fact', 'Unknown')))
                    st.write(f"📌 **{result['type'].upper()}**: {title[:60]}")
            else:
                st.info("No results found")
    
    st.divider()
    
    # Detail level
    detail_level = st.select_slider(
        "Response Length",
        options=["Short", "Medium", "Long", "Very Long"],
        value="Very Long",
        help="Determines how long each response will be"
    )
    
    st.divider()
    
    # Statistics
    st.subheader("📈 Conversation Stats")
    user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
    assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
    total_chars = sum(len(m.get("content", "")) for m in st.session_state.messages)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Questions Asked", user_messages)
        st.metric("Total Characters", f"{total_chars:,}")
    with col2:
        st.metric("Responses", assistant_messages)
        st.metric("Tables Generated", len(st.session_state.tables))
    
    st.divider()
    
    # Quick actions
    st.subheader("🔧 Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Summary", use_container_width=True):
            if len(st.session_state.messages) > 0:
                st.info(f"Total: {len(st.session_state.messages)} messages")
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.success("Cleared!")
            st.rerun()
    
    st.divider()
    
    # Export
    if st.session_state.messages:
        if st.button("📥 Export Chat", use_container_width=True):
            chat_json = json.dumps(st.session_state.messages, indent=2)
            st.download_button(
                "💾 Download JSON",
                chat_json,
                f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                use_container_width=True
            )

# ============= Display Chat =============
st.divider()

# Chat display area
chat_area = st.container(height=500)

with chat_area:
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You:</strong><br>
                {message['content']}
                <div class="message-time">{message.get('timestamp', '').split('T')[1][:5] if message.get('timestamp') else ''}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            content = message['content']
            # Handle both string and list responses
            if isinstance(content, list):
                content = str(content)
            char_count = len(content)
            word_count = len(content.split())
            
            st.markdown(f"""
            <div class="assistant-message">
                <strong>🤖 Assistant:</strong>{' 💡 (Using your knowledge)' if message.get('knowledge_used') else ''}<br>
                {content[:500]}{'...' if len(content) > 500 else ''}
                <div class="response-length">📊 {char_count:,} characters | ~{word_count:,} words</div>
                <div class="message-time">{message.get('timestamp', '').split('T')[1][:5] if message.get('timestamp') else ''}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show full response in expander
            if len(content) > 500:
                with st.expander("📖 Read Full Response"):
                    st.write(content)
                    st.download_button(
                        "📥 Download",
                        content,
                        f"response_{i}.txt",
                        key=f"dl_{i}"
                    )
            
            # Extract and display tables
            tables = extract_tables_from_text(content)
            if tables:
                st.write("**📊 Tables Found:**")
                for j, table_df in enumerate(tables, 1):
                    st.write(f"**Table {j}:**")
                    st.dataframe(table_df, use_container_width=True)
                    
                    # Export options for each table
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        csv = table_df.to_csv(index=False)
                        st.download_button(
                            "📥 CSV",
                            csv,
                            f"table_{i}_{j}.csv",
                            key=f"csv_{i}_{j}"
                        )
                    with col2:
                        json_data = table_df.to_json(orient='records', indent=2)
                        st.download_button(
                            "📥 JSON",
                            json_data,
                            f"table_{i}_{j}.json",
                            key=f"json_{i}_{j}"
                        )
                    with col3:
                        st.write("")  # Placeholder for alignment
                
                # Store tables in session state
                if i < len(st.session_state.messages):
                    message['tables'] = tables
                    if tables not in st.session_state.tables:
                        st.session_state.tables.extend(tables)

# ============= Input Area =============
st.divider()

col1, col2 = st.columns([5, 1])

with col1:
    user_message = st.text_input(
        "Your question:",
        placeholder="Ask anything... Ask for 'essay' or 'detailed' for long responses",
        label_visibility="collapsed"
    )

with col2:
    send_btn = st.button("📤 Send", use_container_width=True, key="send_btn")

# ============= Process Message =============
if send_btn and user_message:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Show processing
    with st.spinner("🔍 Researching your question..."):
        try:
            # Add knowledge context to query
            knowledge_context = ""
            kb_stats = kb.get_stats()
            if kb_stats["total"] > 0:
                knowledge_context = "\n\n" + kb.get_system_context()
            
            # Enhance query with knowledge
            enhanced_query = user_message + knowledge_context
            
            # Get response with knowledge
            result = agent.process_single_query(enhanced_query)
            response = result.get('response', '')
            
            if response:
                # Extract tables from response
                tables = extract_tables_from_text(response)
                
                # Add assistant message
                message_data = {
                    "role": "assistant",
                    "content": response,
                    "query_type": result.get('query_type'),
                    "tools_used": len(result.get('tools_used', [])),
                    "knowledge_used": kb_stats["total"] > 0,
                    "timestamp": datetime.now().isoformat()
                }
                
                if tables:
                    message_data['tables'] = tables
                    st.session_state.tables.extend(tables)
                
                st.session_state.messages.append(message_data)
                st.success("✅ Response generated!")
                logger.info(f"Query processed. Response: {len(response)} chars, Tables: {len(tables)}")
            else:
                st.error("❌ No response generated")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            logger.error(f"Error: {str(e)}")
    
    st.rerun()

# ============= Smart Suggestions =============
if len(st.session_state.messages) == 0:
    st.info("💡 **Get Started** - Try asking:")
    cols = st.columns(3)
    with cols[0]:
        if st.button("📝 Write essay about AI"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Write a comprehensive essay about artificial intelligence",
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()
    with cols[1]:
        if st.button("❓ Explain machine learning"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Explain machine learning in comprehensive detail",
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()
    with cols[2]:
        if st.button("📊 Create table"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Create a table comparing Python, JavaScript, and Java",
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()

# ============= Footer =============
st.divider()
st.caption("""
🤖 **Research ChatBox Pro** | Powered by Claude Opus 4.1
- 🔍 Long detailed responses (up to 32,000 tokens)
- 💬 Full conversation history
- 📥 Export & download results
- ⚡ Instant research answers
""")
