import aiohttp
import asyncio
import json

async def fetch_with_proxy(query="Avengers", limit=20):
    """Función simple para hacer una petición a YTS API usando un proxy"""
    
    proxy = "http://85.143.249.88:3128"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    }

    url = "https://yts.mx/api/v2/list_movies.json"
    params = {
        "query_term": query,
        "limit": limit
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                params=params, 
                headers=headers, 
                proxy=proxy,
                timeout=30
            ) as response:
                print(f"Código de estado: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(data)
                    
                    return True
                else:
                    print(f"Error: {response.status} - {response.reason}")
                    return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False

async def main():
    print("=== PETICIÓN SIMPLE A YTS API CON PROXY ===")
    
    # Puedes cambiar estos parámetros
    query = "Avengers"  # Término de búsqueda
    limit = 20          # Número máximo de resultados
    
    await fetch_with_proxy(query, limit)

if __name__ == "__main__":
    asyncio.run(main())