import streamlit as st
import json
from pipeline import run_pipeline
from AI_filter import load_json
import os

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

# --- Step 1: Landing Page ---
if st.session_state.step == "landing":
    st.title("📰 News Article Filter")
    st.markdown("A simple tool to filter news articles by topic using AI.")
    if st.button("🚀 Start"):
        st.session_state.step = "load"

# --- Step 2: Load Articles & Topic Selection ---
elif st.session_state.step == "load":
    st.header("Step 1: Choose Topic & Load Articles")
    topic = st.text_input("Enter topic to filter for:", value="Artificial Intelligence", key="topic_input")
    fetch_btn = st.button("📡 Fetch Articles Automatically")
    articles_loaded = False
    
    # Create a dedicated area for log display
    log_container = st.container()
    
    if fetch_btn:
        # Create an expander for detailed logging
        with st.expander("View Log Stream", expanded=True):
            # Create a placeholder for real-time progress updates
            progress_container = st.empty()
            
            # Enable Streamlit logging via our custom handler
            from helpers import enable_streamlit_logging
            enable_streamlit_logging(progress_container)
            
            with st.spinner("Running pipeline..."):
                # Run the pipeline with real-time feedback
                run_pipeline(
                    topic=topic, 
                    streamlit_mode=True,
                    streamlit_container=progress_container,
                    verbose=True  # Always show verbose output in Streamlit
                )
            
        st.session_state.pipeline_run = True
        articles_loaded = True
    if articles_loaded or (os.path.exists("output/filtered_articles.json") and st.button("Continue with existing articles")):
        st.session_state.step = "filter"

# --- Step 3: Filter Articles ---
elif st.session_state.step == "filter":
    st.header("Step 2: Filter Articles by Topic")
    topic = st.session_state.get("topic_input", "Artificial Intelligence")
    
    # Create a container for real-time logging
    log_container = st.empty()
    
    # Only run the pipeline if it wasn't run in the previous step
    if not st.session_state.pipeline_run and st.button("Run Filter"):
        with st.spinner("Filtering articles..."):
            # Create a placeholder for real-time progress updates
            progress_container = st.container()
            
            # Run the pipeline with real-time feedback
            run_pipeline(
                topic=topic, 
                streamlit_mode=True,
                streamlit_container=progress_container,
                verbose=True  # Always show verbose output in Streamlit
            )
            
        st.session_state.pipeline_run = True
        
    # If pipeline has been run or filtered articles already exist
    if st.session_state.pipeline_run or os.path.exists("output/filtered_articles.json"):
        filtered_path = "output/filtered_articles.json"
        try:
            filtered_articles = load_json(filtered_path)
            st.session_state.filtered_articles = filtered_articles
            st.success(f"🎯 {len(filtered_articles)} articles found related to *{topic}*!")
            if st.button("Continue to Review"):
                st.session_state.step = "review"
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Could not load filtered articles: {e}")
    else:
        st.info("Click 'Run Filter' to process the articles")

# --- Step 4: Review & Select Articles ---
elif st.session_state.step == "review":
    st.header("Step 3: Review & Select Articles")
    filtered_articles = st.session_state.filtered_articles
    # Get the topic that was used for filtering
    topic = st.session_state.get("topic_input", "Artificial Intelligence")
    
    if not filtered_articles:
        st.warning("No filtered articles to review.")
    else:
        st.write(f"**{len(filtered_articles)} articles found related to '{topic}'.**")
        select_all = st.checkbox("Select All", value=len(st.session_state.selected) == len(filtered_articles))
        if select_all:
            st.session_state.selected = set(range(len(filtered_articles)))
        else:
            st.session_state.selected = set()
        for idx, art in enumerate(filtered_articles):
            checked = idx in st.session_state.selected
            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                if st.checkbox("", value=checked, key=f"sel_{idx}"):
                    st.session_state.selected.add(idx)
                else:
                    st.session_state.selected.discard(idx)
            with col2:
                st.markdown(f"**{art.get('title','(No Title)')}**  \n{art.get('published_date','')}")
                st.write(art.get('content','')[:300] + "...")
                st.write("---")
        st.write(f"Selected: {len(st.session_state.selected)} articles")
        if st.button("💾 Save Selected to Database"):
            from save_db import Article, Session
            session = Session()
            for idx in st.session_state.selected:
                art = filtered_articles[idx]
                db_article = Article(
                    title=art.get("title", ""),
                    link=art.get("link", ""),
                    category=art.get("category", ""),
                    topic=topic,  # Add the topic here
                    published_date=art.get("published_date"),
                    updated_date=art.get("updated_date"),
                    content=art.get("content", "")
                )
                session.add(db_article)
            session.commit()
            session.close()
            st.success(f"✅ Selected articles saved to database with topic '{topic}'.")
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