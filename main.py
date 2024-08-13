import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import requests # For Bing web search
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException # For capturing errors
import os # For console logging
import time # For sleep on retry 
import re # For stripping HTML

# Load environment variables from the .env file
load_dotenv()

# Initialize the OpenAI client
openai = OpenAI()

# Set up the Streamlit interface
st.title('AI Report Generator')
st.write('Enter a question or topic for your report:')

# Retrieve the Bing API key from environment variables
bing_api_key = os.getenv("BING_API_KEY")

# Define the Semantic Scholar API endpoint
semantic_url = "https://api.semanticscholar.org/graph/v1/paper/search"

# Get the user input for the question or topic
topic = st.text_input('Question/Topic')

# Define a global variable for max tokens
MAX_TOKENS = 3000

# Define a function to log messages to the console
def log_message(label, message):
    os.write(1, f"{label}: {message}\n\n".encode())

# Function to strip HTML tags from a string
def strip_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


# Define a function to fetch a response from OpenAI's API
def fetch_openai_response(prompt, max_tokens=MAX_TOKENS):
    log_message("Prompt", prompt)
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            temperature=0.2,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        log_message("OpenAI API error", str(e))
        return {"error": "Failed to fetch response from OpenAI API"}


# Define a function to perform a web search using Bing's API
def search_web(query):
    log_message("Bing query", query)
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": bing_api_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML"}

    for attempt in range(3):
        try:
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            if results.get('webPages'):
                # Strip HTML tags from the snippets
                for result in results['webPages']['value']:
                    result['snippet'] = strip_html_tags(result['snippet'])
                return results
        except HTTPError as http_err:
            log_message("HTTP error occurred", str(http_err))
        except ConnectionError as conn_err:
            log_message("Connection error occurred", str(conn_err))
        except Timeout as timeout_err:
            log_message("Timeout error occurred", str(timeout_err))
        except RequestException as req_err:
            log_message("Request error occurred", str(req_err))
        time.sleep(1)
    return {"error": "Failed to retrieve web results after 3 attempts"}


# Define a function to search for academic papers using the Semantic Scholar API
def search_papers(query):
    log_message("Search papers query", query)
    headers = {"Content-Type": "application/json"}
    params = {"query": query, "fields": "title,authors,year,url", "limit": 3}

    for attempt in range(3):
        try:
            response = requests.get(semantic_url, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            if 'data' in results and results['data']:
                return results
        except HTTPError as http_err:
            log_message("HTTP error occurred", str(http_err))
        except ConnectionError as conn_err:
            log_message("Connection error occurred", str(conn_err))
        except Timeout as timeout_err:
            log_message("Timeout error occurred", str(timeout_err))
        except RequestException as req_err:
            log_message("Request error occurred", str(req_err))
        time.sleep(1)
    return {"error": "Failed to retrieve papers after 3 attempts"}


# Initialize an empty list to store URLs
result_urls = []

# Main logic to be executed when the user clicks the 'Search' button
if st.button('Search'):
    if topic:
        refined_query = fetch_openai_response(f"Refine the following search query to make it more specific: {topic}",
                                              max_tokens=MAX_TOKENS)
        st.write("Refined Query:", refined_query)

        search_results = search_web(refined_query)
        if search_results.get('webPages'):
            for result in search_results['webPages']['value']:
                # Append the URL to the list
                if (result_urls.append(result['url'])):
                    result_urls.append(result['url'])
        else:
            st.write("No web results found.")

        # Refined topic for paper search in list form (for better results)
        refined_topic = fetch_openai_response(f"Turn this into a comma separated list of three or less relevant "
                                              f"key words: {topic}",
                                              max_tokens=MAX_TOKENS)
        paper_result = search_papers(refined_topic)
        if 'data' in paper_result and paper_result['data']:
            for paper in paper_result['data']:
                # Append the URL to the list
                if (result_urls.append(paper['url'])):
                    result_urls.append(paper['url'])
        else:
            st.write("No papers found.")

        # Convert the result_urls list to a string
        urls_string = ", ".join(result_urls)
        
        short_article = fetch_openai_response(
            f"Write a short article about the subject or answering the question, including formal citations to the "
            f"relevant papers at the bottom. Use the following URLs as references: {urls_string}. The question: {topic}")
        st.write("---")
        st.write(short_article)

        feedback = fetch_openai_response(
            f"Provide editorial feedback on the following article, noting any problems, areas of improvement, "
            f"or inaccuracies in article. Keeping it 500 characters or less: {short_article}")
        st.write("---")
        st.subheader("Feedback")
        st.write(feedback)

        comment = fetch_openai_response(
            f"Write a response to and comment on the following article, ie like a web critic's comment on a "
            f"blog post. Add specific suggestions: {short_article}")
        st.write("---")
        st.subheader("Critic's Comments")
        st.write(comment)

        rewrite = fetch_openai_response(
            f"Rewrite the following article incorporating this editorial feedback comments: {feedback} -- "
            f"Use the following URLs as references: {urls_string}. Make sure to add references at the end of the story. "
            f"The article to rewrite: {short_article}")
        st.write("---")
        st.subheader("Rewrite Based on Critic's Comments")
        st.write(rewrite)

        critic = fetch_openai_response(
            f"Respond to this critic's comments about the following short article. Include references. The feedback: {feedback} -- "
            f"The article to reference: {short_article} The rewritten article to reference: {rewrite}")
        st.write("---")
        st.subheader("Response to Critic")
        st.write(critic)

        st.write("---")
        st.subheader("Full citation details for the academic papers and web sources")
        if search_results.get('webPages'):
            st.write("---")
            st.write("Web Results:")
            for result in search_results['webPages']['value']:
                st.write(f"**Title**: {result['name']}")
                st.write(f"**URL**: {result['url']}")
                st.write(f"**Snippet**: {result['snippet']}")
                st.write("")
            all_snippets = " ".join([result['snippet'] for result in search_results['webPages']['value']])
            summary = fetch_openai_response(f"Summarize the following content: {all_snippets}", max_tokens=MAX_TOKENS)
            st.write(f"**Summary**: {summary}")
        else:
            st.write("No web results found.")

        paper_result = search_papers(refined_topic)
        if 'data' in paper_result and paper_result['data']:
            st.write("---")
            st.write("Academic Papers:")
            for paper in paper_result['data']:
                st.write(f"**Title**: {paper['title']}")
                st.write(f"**Authors**: {', '.join(author['name'] for author in paper['authors'])}")
                st.write(f"**Year**: {paper['year']}")
                st.write(f"**URL**: {paper['url']}")
                st.write("")
        else:
            st.write("No papers found.")
    else:
        st.write("Please enter a question or topic.")
