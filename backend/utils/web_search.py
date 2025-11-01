from ddgs import DDGS
import re

def perform_web_search(query: str, num_results: int = 5, language: str = "en"):
    """
    Perform a web search using DuckDuckGo (ddgs) and return contextually relevant, 
    cleaned English results.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))

        clean_results = []

        for r in results:
            # --- Basic validation ---
            if not r or "href" not in r or not r.get("title"):
                continue
            if "zhihu" in r["href"] or "baidu" in r["href"]:
                continue  # skip obvious non-English sources

            snippet = r.get("body", "").strip()
            title = r["title"].strip()
            
            # --- Text cleanup ---
            snippet = re.sub(r'\s+', ' ', snippet)  # normalize spaces
            snippet = re.sub(r'\.{2,}', '.', snippet)  # fix ellipses
            snippet = re.sub(r'\|.*', '', snippet)  # drop trailing site info
            snippet = snippet.replace("Read more", "").replace("Learn more", "")
            snippet = snippet.replace("...", "").strip()

            # --- Context filter ---
            # Keep only results that mention key terms from the query
            query_keywords = [word.lower() for word in re.findall(r'\w+', query) if len(word) > 3]
            if not any(k in snippet.lower() or k in title.lower() for k in query_keywords):
                continue

            clean_results.append({
                "title": title,
                "snippet": snippet,
                "link": r["href"]
            })

        if not clean_results:
            return [{"title": "No relevant English results found", "snippet": "", "link": ""}]

        # --- Make the text suitable for LLM context ---
        context_string = "\n\n".join([
            f"🔹 **{item['title']}**\n{item['snippet']}\nSource: {item['link']}"
            for item in clean_results
        ])

        return context_string

    except Exception as e:
        return f"⚠️ Error fetching web data: {e}"
