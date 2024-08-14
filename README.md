# AI Report Generator
A recursive enriched AI report generator running in Python Streamlit that pulls URLs from Semantic Scholar and Bing search generates a report using the URLs, evaluates and provides feedback on the initially generated report, and then integrates the feedback with complete citations.

It's a basic design/experiment to provide a very simple clone of Perplexity.ai (I am not affiliated with Perplexity.ai in any way) that you can extend and enhance however you want.

# Getting started 

- install `poetry` if needed https://python-poetry.org/docs/#installing-with-pipx
- `poetry install`
- `poetry shell`
- create a `.env` file with `OPENAI_API_KEY=YOUR_API_KEY`
- create a `.env` file with `BING_API_KEY=BING_API_KEYY`
- `streamlit run main.py`

# Examples

- Why are black holes black, or are they?
- What makes the sky blue?
- What's the history of logic? 
- Why are there Clowns all around San Francisco on April 1st?

# Other Options
- Set MAX_TOKENS in .env (defaults to 3000)
- Set MULTISET_OPTIONS in .env (useful for troubleshooting when set to YES. Defaults to NO)