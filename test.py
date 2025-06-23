import aiohttp
import asyncio
import json
import time

# Lista de proxies para probar (reemplaza con tus propios proxies)
PROXIES_TO_TEST = [
    "http://134.90.246.28:8080",         # Reemplaza con tu proxy 1
    "http://102.209.148.10",         # Reemplaza con tu proxy 2
    "http://9.10.11.12:80",        # Reemplaza con tu proxy 3
    # Añade más proxies aquí
]

# Si necesitas proxies con autenticación, usa este formato:
# "http://usuario:contraseña@1.2.3.4:8080"

async def test_proxy(proxy):
    """Prueba un proxy individual con la API de YTS"""
    # Encabezados exactos como en tu navegador
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "es,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Linux\"",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    url = "https://yts.mx/api/v2/list_movies.json"
    params = {"query_term": "Avengers", "limit": 5}
    
    try:
        print(f"Probando con proxy: {proxy}")
        start_time = time.time()
        
        # Crear sesión con proxy
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                params=params, 
                headers=headers, 
                proxy=proxy,
                timeout=20  # Aumentar timeout para proxies lentos
            ) as response:
                duration = time.time() - start_time
                
                print(f"Código de estado: {response.status}, Tiempo: {duration:.2f}s")
                
                if response.status == 200:
                    data = await response.json()
                    print("¡ÉXITO! Respuesta recibida correctamente")
                    
                    movie_count = data.get("data", {}).get("movie_count", 0)
                    print(f"Películas encontradas: {movie_count}")
                    
                    # Guardar la respuesta y el proxy exitoso
                    with open("yts_response.json", "w") as f:
                        json.dump(data, f, indent=2)
                    
                    with open("working_proxy.txt", "w") as f:
                        f.write(proxy)
                    
                    print(f"Proxy exitoso guardado en working_proxy.txt")
                    
                    return True
                else:
                    print(f"Error: {response.status} - {response.reason}")
                    return False
                    
    except Exception as e:
        print(f"Error al usar el proxy {proxy}: {type(e).__name__}: {str(e)}")
        return False

async def test_without_proxy():
    """Prueba la conexión directa sin proxy"""
    print("\n=== PRUEBA SIN PROXY ===")
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "es,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Linux\"",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    url = "https://yts.mx/api/v2/list_movies.json"
    params = {"query_term": "Avengers", "limit": 5}
    
    try:
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=30) as response:
                duration = time.time() - start_time
                
                print(f"Código de estado: {response.status}, Tiempo: {duration:.2f}s")
                
                if response.status == 200:
                    data = await response.json()
                    print("ÉXITO! La conexión directa funciona.")
                    
                    movie_count = data.get("data", {}).get("movie_count", 0)
                    print(f"Películas encontradas: {movie_count}")
                    
                    # Guardar la respuesta
                    with open("yts_response_direct.json", "w") as f:
                        json.dump(data, f, indent=2)
                    
                    return True
                else:
                    print(f"Error: {response.status} - {response.reason}")
                    return False
                    
    except Exception as e:
        print(f"Error en conexión directa: {type(e).__name__}: {str(e)}")
        return False

async def main():
    print("=== TEST DE API YTS CON PROXIES PERSONALIZADOS ===")
    
    # Primero probar sin proxy
    direct_success = await test_without_proxy()
    
    if direct_success:
        print("\nLa conexión directa funciona! No es necesario usar proxies.")
        return
    
    print("\n=== PRUEBAS CON PROXIES ===")
    
    # Probar cada proxy de la lista
    for proxy in PROXIES_TO_TEST:
        success = await test_proxy(proxy)
        if success:
            print(f"\n¡Proxy {proxy} funcionó correctamente!")
            # Implementar la solución en el código principal usando este proxy
            print("Puedes usar este proxy en tu aplicación principal")
            break
        # Pequeña pausa entre pruebas
        await asyncio.sleep(1)
    else:
        print("\nNinguno de los proxies funcionó :(")
        print("Sugerencias:")
        print("1. Intenta con otros proxies")
        print("2. Verifica si los proxies requieren autenticación")
        print("3. Considera usar un servicio de proxy comercial o VPN")

if __name__ == "__main__":
    asyncio.run(main())