import requests

def analyze_with_crewai(text):
    # Use CrewAI to analyze the extracted text and get recommendations
    # Example: This function should interact with CrewAI's API
    response = requests.post('https://api.cohere.ai/analyze', json={'text': text})
    
    if response.status_code == 200:
        data = response.json()
        recommendations = data.get('recommendations', 'No recommendations found.')
        articles = data.get('articles', [])
        return recommendations, articles
    else:
        return 'Error in analysis', []
