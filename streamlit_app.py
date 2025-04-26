import streamlit as st
import json
import os
from cli_pipeline import run_cli_pipeline
from AI_filter import filter_articles
from save_db import Article, Session, init_db
from datetime import datetime

st.set_page_config(page_title="News Article Filter", page_icon="📰", layout="centered")

# --- Session State for Navigation ---
if "step" not in st.session_state:
    st.session_state.step = "landing"
if "filtered_articles" not in st.session_state:
    st.session_state.filtered_articles = []
if "selected" not in st.session_state:
    st.session_state.selected = set()
if "pipeline_run" not in st.session_state:
    st.session_state.pipeline_run = False
if "topic" not in st.session_state:
    st.session_state.topic = "Artificial Intelligence"  # Default topic
if "is_fetching" not in st.session_state:
    st.session_state.is_fetching = False

def return_to_main():
    # Reset all necessary session state variables except step
    st.session_state.is_fetching = False
    st.session_state.filtered_articles = []
    st.session_state.selected = set()
    st.session_state.pipeline_run = False
    st.session_state.step = "load"  # Go directly to load step

# Function to show main menu button
def show_main_menu_button():
    # Show on filter and review steps
    if st.session_state.step in ["filter", "review"]:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.button("🏠 Main Menu", on_click=return_to_main)

def start_fetching():
    st.session_state.is_fetching = True

# Function to load articles from file
def load_existing_articles(file_path="output/articles.json"):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                articles = json.load(f)
            return articles, len(articles) > 0
        return [], False
    except Exception as e:
        st.error(f"Error loading articles: {e}")
        return [], False

# --- Step 1: Landing Page ---
if st.session_state.step == "landing":
    st.title("📰 News Article Filter")
    st.markdown("A simple tool to filter news articles by topic using AI.")
    if st.button("🚀 Start"):
        st.session_state.step = "load"

# --- Step 2: Load Articles & Topic Selection ---
elif st.session_state.step == "load":
    st.header("Step 1: Load Articles")
    
    col1, col2 = st.columns(2)
    with col1:
        fetch_btn = st.button("📡 Fetch New Articles", 
                            disabled=st.session_state.is_fetching,
                            on_click=start_fetching)
        if st.session_state.is_fetching:
            st.info("Fetching articles in progress...")
    with col2:
        # Only show continue button if articles exist
        articles_exist = os.path.exists("output/articles_with_content.json")
        continue_btn = st.button("📂 Use Existing Articles", 
                               disabled=not articles_exist or st.session_state.is_fetching)
        if not articles_exist:
            st.caption("No existing articles found")
    
    if st.session_state.is_fetching:
        try:
            # Create an expander for detailed logging
            with st.expander("View Log Stream", expanded=True):
                # Create a container for the log display
                log_container = st.empty()
                
                # Initialize or clear log messages
                st.session_state.log_messages = []
                
                # Custom handler for Streamlit logging
                def log_callback(message):
                    st.session_state.log_messages.append(message)
                    # Update the log display with just the new message
                    log_container.text_area(
                        "Latest Logs",
                        value="\n".join(st.session_state.log_messages[-10:]),
                        height=400,
                        disabled=True
                    )
                    
                with st.spinner("Fetching and processing articles..."):
                    # Run the pipeline with real-time feedback
                    success = run_cli_pipeline(
                        topic=st.session_state.topic,
                        verbose=True,
                        log_callback=log_callback
                    )
                    
                    if success:
                        # Load articles with content
                        articles_file = "output/articles_with_content.json"
                        if os.path.exists(articles_file):
                            with open(articles_file, 'r', encoding='utf-8') as f:
                                articles = json.load(f)
                                if articles:
                                    st.session_state.raw_articles = articles
                                    st.session_state.pipeline_run = True
                                    st.success(f"Successfully fetched {len(articles)} articles with content!")
                                    st.session_state.is_fetching = False
                                    st.session_state.step = "filter"
                                    st.rerun()
                                else:
                                    st.error("No articles with content were found.")
                                    st.session_state.is_fetching = False
                        else:
                            st.error("Failed to load articles after fetching. Please try again.")
                            st.session_state.is_fetching = False
                    else:
                        st.error("Failed to fetch articles. Please try again.")
                        st.session_state.is_fetching = False
                        
        except Exception as e:
            st.error(f"An error occurred while fetching articles: {str(e)}")
            st.session_state.pipeline_run = False
            st.session_state.is_fetching = False
    
    if continue_btn:
        try:
            articles_file = "output/articles_with_content.json"
            if os.path.exists(articles_file):
                with open(articles_file, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                    if articles:
                        # Store articles in session state
                        st.session_state.raw_articles = articles
                        st.session_state.pipeline_run = True
                        st.success(f"Loaded {len(articles)} existing articles with content!")
                        st.session_state.step = "filter"
                        st.rerun()
                    else:
                        st.error("No articles with content found in the existing file.")
            else:
                st.error(f"No articles with content found. Try fetching new articles instead.")
        except Exception as e:
            st.error(f"An error occurred while loading articles: {str(e)}")
            st.session_state.pipeline_run = False

# --- Step 3: Filter Articles ---
elif st.session_state.step == "filter":
    show_main_menu_button()
    st.header("Step 2: Filter Articles by Topic")
    
    # Check if we have raw articles to filter
    if not hasattr(st.session_state, 'raw_articles'):
        st.error("No articles loaded. Please go back and load articles first.")
        if st.button("← Back to Load Articles"):
            st.session_state.step = "load"
            st.rerun()
    else:
        # Show total articles loaded
        total_articles = len(st.session_state.raw_articles)
        st.info(f"📚 {total_articles} articles loaded")
        
        # Topic input with validation
        topic = st.text_input(
            "Enter topic to filter for:",
            value=st.session_state.topic,
            key="topic_input"
        )
        if topic.strip():  # Update session state only if topic is not empty
            st.session_state.topic = topic.strip()
        
        # Show AI filter button
        if st.button("🤖 Run AI Filter"):
            if not st.session_state.topic:
                st.error("Please enter a topic for AI filtering")
            else:
                with st.spinner(f"AI is filtering articles for topic: {st.session_state.topic}..."):
                    try:
                        # Load articles with content
                        articles_with_content_file = "output/articles_with_content.json"
                        if not os.path.exists(articles_with_content_file):
                            st.error("No articles with content found. Please try fetching articles again.")
                            st.session_state.filtered_articles = []
                            st.session_state.current_topic = st.session_state.topic
                        else:
                            with open(articles_with_content_file, 'r', encoding='utf-8') as f:
                                articles_with_content = json.load(f)
                            
                            # Filter the articles using AI
                            filtered_articles = filter_articles(
                                articles_with_content,  # Use articles with content
                                topic=st.session_state.topic,
                                streamlit_mode=True
                            )
                            
                            # Store filtered results and topic
                            st.session_state.filtered_articles = filtered_articles
                            st.session_state.current_topic = st.session_state.topic
                            
                            # Save filtered articles to a JSON file
                            output_dir = "output"
                            if not os.path.exists(output_dir):
                                os.makedirs(output_dir)
                            
                            filtered_file = os.path.join(output_dir, f"filtered_articles_{st.session_state.topic.lower().replace(' ', '_')}.json")
                            with open(filtered_file, 'w', encoding='utf-8') as f:
                                json.dump(filtered_articles, f, indent=4, ensure_ascii=False)
                            
                            if filtered_articles:
                                st.success(f"🎯 {len(filtered_articles)} articles found related to *{st.session_state.topic}*!")
                            else:
                                st.warning(f"No articles found matching the topic: {st.session_state.topic}")
                                
                    except Exception as e:
                        st.error(f"An error occurred while filtering articles: {str(e)}")
                        st.session_state.filtered_articles = []
        
        # If we have filtered articles, show the continue button
        if 'filtered_articles' in st.session_state:
            filtered_count = len(st.session_state.filtered_articles)
            if filtered_count > 0:
                if st.button("Continue to Review"):
                    st.session_state.step = "review"
                    st.rerun()
            else:
                st.info("Try filtering with a different topic")

# --- Step 4: Review & Select Articles ---
elif st.session_state.step == "review":
    show_main_menu_button()
    st.header("Step 3: Review & Select Articles")
    filtered_articles = st.session_state.filtered_articles
    topic = st.session_state.get("current_topic", "")
    
    if not filtered_articles:
        st.warning("No filtered articles to review.")
    else:
        st.write(f"**{len(filtered_articles)} articles found related to '{topic}'**")
        select_all = st.checkbox("Select/Deselect All Articles", value=len(st.session_state.selected) == len(filtered_articles))
        if select_all:
            st.session_state.selected = set(range(len(filtered_articles)))
        else:
            st.session_state.selected = set()
        
        for idx, art in enumerate(filtered_articles):
            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                article_title = art.get('title', '(No Title)')[:20] + "..."
                if st.checkbox(
                    label=f"Select article: {article_title}",
                    value=idx in st.session_state.selected,
                    key=f"sel_{idx}",
                    label_visibility="collapsed"
                ):
                    st.session_state.selected.add(idx)
                else:
                    st.session_state.selected.discard(idx)
            with col2:
                st.markdown(f"**{art.get('title','(No Title)')}**  \n{art.get('published_date','')}")
                st.write(art.get('content','')[:300] + "...")
                st.write("---")
        
        st.write(f"Selected: {len(st.session_state.selected)} articles")
        if st.button("💾 Save Selected to Database"):
            try:
                # Initialize database
                if init_db():
                    session = Session()
                    for idx in st.session_state.selected:
                        art = filtered_articles[idx]
                        # Convert string dates to datetime objects
                        published_date = None
                        updated_date = None
                        if art.get("published_date"):
                            published_date = datetime.fromisoformat(art["published_date"].replace("Z", "+00:00"))
                        if art.get("updated_date"):
                            updated_date = datetime.fromisoformat(art["updated_date"].replace("Z", "+00:00"))
                        
                        db_article = Article(
                            title=art.get("title", ""),
                            link=art.get("link", ""),
                            category=art.get("category", ""),
                            topic=topic,
                            published_date=published_date,
                            updated_date=updated_date,
                            content=art.get("content", "")
                        )
                        session.add(db_article)
                    session.commit()
                    session.close()
                    st.success(f"✅ Selected articles saved to database with topic '{topic}'.")
                else:
                    st.error("Failed to initialize database connection.")
            except Exception as e:
                st.error(f"Failed to save articles to database: {e}")
                if 'session' in locals():
                    session.rollback()
                    session.close()
                
        if st.button("📄 Export Selected to JSON"):
            selected_arts = [filtered_articles[idx] for idx in st.session_state.selected]
            # Add topic to each exported article
            for art in selected_arts:
                art["topic"] = topic
            st.download_button(
                label="Download Selected Articles as JSON",
                data=json.dumps(selected_arts, indent=2, ensure_ascii=False),
                file_name=f"selected_articles_{topic.lower().replace(' ', '_')}.json",
                mime="application/json"
            )