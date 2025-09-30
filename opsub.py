import requests
import json

def get_single_subtitle_per_language():
    """
    Test script to get exactly 1 subtitle in Spanish and 1 in English
    Returns the first URL found for each language
    """
    
    # API configuration
    api_key = "0sILs5rixHqzce8Yfhuws3yyHG8MhWFR"
    base_url = "https://api.opensubtitles.com/api/v1/subtitles"
    imdb_id = "tt0082198"  # The Matrix
    
    headers = {
        'Api-Key': api_key,
        'User-Agent': 'MiApp v1.0',
        'Accept': 'application/json'
    }
    
    results = {}
    
    # Get Spanish subtitle
    print("Fetching Spanish subtitle...")
    params_es = {
        'imdb_id': imdb_id,
        'languages': 'es',
        'per_page': 1,
        'order_by': 'ratings',
        'order_direction': 'desc'
    }
    
    try:
        response_es = requests.get(base_url, headers=headers, params=params_es)
        response_es.raise_for_status()
        data_es = response_es.json()
        
        if data_es.get('data') and len(data_es['data']) > 0:
            first_es = data_es['data'][0]
            results['spanish'] = {
                'id': first_es['id'],
                'language': first_es['attributes']['language'],
                'url': first_es['attributes']['url'],
                'release': first_es['attributes']['release'],
                'download_count': first_es['attributes']['download_count'],
                'file_id': first_es['attributes']['files'][0]['file_id'] if first_es['attributes']['files'] else None
            }
            print(f"Spanish subtitle found: {results['spanish']['release']}")
            #print(f"Full data: {json.dumps(first_es, indent=2)}")
        else:
            print("No Spanish subtitles found")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Spanish subtitles: {e}")
    
    # Get English subtitle
    print("\nFetching English subtitle...")
    params_en = {
        'imdb_id': imdb_id,
        'languages': 'en',
        'per_page': 1,
        'order_by': 'download_count',
        'order_direction': 'desc'
    }
    
    try:
        response_en = requests.get(base_url, headers=headers, params=params_en)
        response_en.raise_for_status()
        data_en = response_en.json()
        
        if data_en.get('data') and len(data_en['data']) > 0:
            first_en = data_en['data'][0]
            results['english'] = {
                'id': first_en['id'],
                'language': first_en['attributes']['language'],
                'url': first_en['attributes']['url'],
                'release': first_en['attributes']['release'],
                'download_count': first_en['attributes']['download_count'],
                'file_id': first_en['attributes']['files'][0]['file_id'] if first_en['attributes']['files'] else None
            }
            print(f"English subtitle found: {results['english']['release']}")
        else:
            print("No English subtitles found")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching English subtitles: {e}")
    
    return results

def download_subtitle(file_id, filename="subtitle.srt"):
    """
    Download subtitle file using the file_id
    """
    api_key = "0sILs5rixHqzce8Yfhuws3yyHG8MhWFR"
    download_url = "https://api.opensubtitles.com/api/v1/download"
    
    headers = {
        'Api-Key': api_key,
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ4cTlaQ1UxYkppcGpEWkJYVnFVVnR1ZENUb1NTWlpHaSIsImV4cCI6MTc1ODg2ODc1MH0.UEpCHaIq2VZJ3yUmgNszW06NUw49-k5brAFgtq6q5rs',
        'User-Agent': 'MiApp v1.0',
        'Accept': 'application/json'
    }
    
    data = {
        'file_id': 7937412,
        'sub_format': 'srt',

            }
            
    try:
        print(f"Downloading subtitle with file_id: {file_id}")
        response = requests.post(download_url, headers=headers, json=data)
        response.raise_for_status()
        
        download_info = response.json()
        print(f"Download info: {json.dumps(download_info, indent=2)}")
        
        if 'link' in download_info:
            # Download the actual file
            file_response = requests.get(download_info['link'])
            file_response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(file_response.content)
            
            print(f"Subtitle downloaded successfully as: {filename}")
            return filename
        else:
            print("Download link not found in response")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error downloading subtitle: {e}")
        return None

def main():
    print("OpenSubtitles API Test - Single Result Per Language")
    print("=" * 55)
    
    subtitles = get_single_subtitle_per_language()
    
    print("\n" + "=" * 55)
    print("RESULTS:")
    print("=" * 55)
    
    if 'spanish' in subtitles:
        print(f"\nSPANISH SUBTITLE:")
        print(f"ID: {subtitles['spanish']['id']}")
        print(f"Release: {subtitles['spanish']['release']}")
        print(f"Downloads: {subtitles['spanish']['download_count']}")
        print(f"URL: {subtitles['spanish']['url']}")
        
        # Try to download Spanish subtitle
        if 'file_id' in subtitles['spanish']:
            download_subtitle(subtitles['spanish']['file_id'], "spanish.srt")
    
    if 'english' in subtitles:
        print(f"\nENGLISH SUBTITLE:")
        print(f"ID: {subtitles['english']['id']}")
        print(f"Release: {subtitles['english']['release']}")
        print(f"Downloads: {subtitles['english']['download_count']}")
        print(f"URL: {subtitles['english']['url']}")
        
        # Try to download English subtitle
        if 'file_id' in subtitles['english']:
            download_subtitle(subtitles['english']['file_id'], "english.srt")
    
    # Return just the first URL as requested
    if 'spanish' in subtitles:
        print(f"\nFirst URL (Spanish): {subtitles['spanish']['url']}")
        return subtitles['spanish']['url']
    elif 'english' in subtitles:
        print(f"\nFirst URL (English): {subtitles['english']['url']}")
        return subtitles['english']['url']
    else:
        print("\nNo subtitles found")
        return None

if __name__ == "__main__":
    first_url = main()