import requests
import json

def fetch_with_proxy(query="Avengers", limit=5):
    # Proxy que funcionó con aiohttp
    proxy = "http://102.209.148.10:8080"
    
    # Configuración exacta de proxies
    proxies = {
        "http": proxy,
        "https": proxy
    }
    
    # Usa exactamente los mismos encabezados que funcionaron con aiohttp
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es,en;q=0.9",
        "Cache-Control": "max-age=0"
    }
    
    url = "https://yts.mx/api/v2/list_movies.json"
    params = {
        "query_term": query,
        "limit": limit
    }
    
    try:
        # Configurar un timeout más largo, y permitir redirecciones
        response = requests.get(
            url, 
            params=params, 
            headers=headers, 
            proxies=proxies,
            timeout=45,
            allow_redirects=True,
            verify=False  # Desactivar verificación SSL (solo para pruebas)
        )
        
        print(f"Código de estado: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Respuesta exitosa!")
            return data
        else:
            print(f"Error: {response.status_code} - {response.reason}")
            return None
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return None

if __name__ == "__main__":
    result = fetch_with_proxy("Avengers", 5)
    if result:
        print("Petición exitosa!")