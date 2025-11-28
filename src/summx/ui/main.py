import asyncio
import streamlit as st

from summx.agent import PaperAgent, PlanExecutor, QueryPlanner
from summx.config import load_config
from summx.llm import get_llm
from summx.sources import get_source_client

# --- Page Config ---
st.set_page_config(
    page_title="SummX: AI Paper Assistant",
    page_icon="🤖",
    layout="wide",
)

# --- Agent Setup ---
# This part is similar to the CLI's setup, but adapted for Streamlit's async capabilities.
# We don't cache the agent anymore, as it now depends on the UI's state.
def get_agent(planner_provider, summarizer_provider):
    """Create the PaperAgent instance based on UI selections."""
    config = load_config()
    planner_llm = get_llm(provider=planner_provider, config=config)
    summarizer_llm = get_llm(provider=summarizer_provider, config=config)
    source_client = get_source_client(config=config)
    planner = QueryPlanner(llm=planner_llm)
    executor = PlanExecutor(source_client=source_client, summarizer_llm=summarizer_llm)
    return PaperAgent(planner=planner, executor=executor)

# --- UI Layout ---
st.title("🤖 SummX: Your AI Research Assistant")
st.write("Enter a query to search for and summarize academic papers from arXiv.")

with st.sidebar:
    st.header("Configuration")
    planner_provider = st.selectbox("Planner LLM", ["openai", "groq", "dummy"], index=0)
    summarizer_provider = st.selectbox("Summarizer LLM", ["groq", "openai", "dummy"], index=0)

query = st.text_input("Search Query", placeholder="e.g., 'five most recent papers on hyper graphs'")

if st.button("Search"):
    if not query:
        st.warning("Please enter a search query.")
    else:
        agent = get_agent(planner_provider, summarizer_provider)
        with st.spinner("Finding and summarizing papers..."):
            try:
                # Run the agent's async method in Streamlit's event loop
                plan, results = asyncio.run(agent.run(query))

                st.header("Results")
                if not results:
                    st.info("No papers found matching your query.")
                else:
                    for result in results:
                        st.subheader(result.meta.title)
                        st.caption(f"_by {', '.join(result.meta.authors)}_ | Published: {result.meta.published}")
                        st.markdown(f"[Read PDF]({result.meta.pdf_url})")
                        if result.summary:
                            with st.expander("View Summary"):
                                st.markdown(result.summary.to_markdown())
                        st.divider()

            except Exception as e:
                st.error(f"An error occurred: {e}")
