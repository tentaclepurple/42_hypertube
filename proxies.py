import aiohttp
import asyncio
import time
import os
from typing import List, Dict, Any, Optional

async def test_proxy(proxy: str, timeout: int = 20) -> Optional[Dict[str, Any]]:
    """
    Prueba un proxy individual con la API de YTS
    
    Args:
        proxy: La URL del proxy (http://host:port, socks4://host:port, etc.)
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        La respuesta JSON si tiene éxito, None si falla
    """
    # Encabezados de navegador
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es,en;q=0.9",
        "Cache-Control": "max-age=0"
    }
    
    url = "https://yts.mx/api/v2/list_movies.json"
    params = {"query_term": "Avengers", "limit": 2}  # Solo 2 resultados para que sea más rápido
    
    try:
        print(f"\nProbando proxy: {proxy}")
        start_time = time.time()
        
        if proxy.startswith('socks'):
            # Para proxies SOCKS necesitamos aiohttp-socks
            try:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxy)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(
                        url, 
                        params=params, 
                        headers=headers, 
                        timeout=timeout
                    ) as response:
                        duration = time.time() - start_time
                        status = response.status
            except ImportError:
                print("⚠️ Para usar proxies SOCKS, instala aiohttp-socks: pip install aiohttp-socks")
                return None
        else:
            # Para proxies HTTP regulares
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    proxy=proxy,
                    timeout=timeout,
                    ssl=False  # Desactivar verificación SSL
                ) as response:
                    duration = time.time() - start_time
                    status = response.status
        
        print(f"  Resultado: Status {status}, tiempo: {duration:.2f}s")
        
        if status == 200:
            data = await response.json()
            movie_count = data.get("data", {}).get("movie_count", 0)
            print(f"  ✅ ÉXITO! Películas encontradas: {movie_count}")
            return data
        else:
            print(f"  ❌ Error: {status}")
            return None
            
    except asyncio.TimeoutError:
        duration = time.time() - start_time
        print(f"  ❌ Timeout después de {duration:.2f}s")
        return None
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {str(e)}")
        return None

async def test_proxies_from_file(file_path: str, max_concurrent: int = 5, save_working: bool = True):
    """
    Prueba múltiples proxies desde un archivo
    
    Args:
        file_path: Ruta al archivo con la lista de proxies
        max_concurrent: Número máximo de pruebas concurrentes
        save_working: Si es True, guarda los proxies que funcionan
    """
    if not os.path.exists(file_path):
        print(f"Error: El archivo {file_path} no existe")
        return
    
    # Leer la lista de proxies
    with open(file_path, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    
    print(f"Cargados {len(proxies)} proxies del archivo {file_path}")
    
    # Crear archivo para guardar proxies que funcionan
    working_proxies_path = "working_proxies.txt"
    if save_working:
        with open(working_proxies_path, 'w') as f:
            f.write("# Proxies que funcionan - Generado por proxy_tester.py\n")
            f.write(f"# Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Función para probar un lote de proxies concurrentemente
    async def test_proxy_batch(proxy_batch):
        tasks = []
        for proxy in proxy_batch:
            tasks.append(test_proxy(proxy))
        return await asyncio.gather(*tasks)
    
    # Dividir la lista en lotes para no sobrecargar
    results = []
    working_count = 0
    
    for i in range(0, len(proxies), max_concurrent):
        batch = proxies[i:i+max_concurrent]
        print(f"\nProbando lote {i//max_concurrent + 1}/{len(proxies)//max_concurrent + 1} ({len(batch)} proxies)")
        
        batch_results = await test_proxy_batch(batch)
        
        for j, result in enumerate(batch_results):
            proxy = batch[j]
            if result is not None:
                # Guardar proxy que funciona
                if save_working:
                    with open(working_proxies_path, 'a') as f:
                        f.write(f"{proxy}\n")
                working_count += 1
        
        results.extend(batch_results)
        
        # Pequeña pausa entre lotes para evitar sobrecargas
        if i + max_concurrent < len(proxies):
            await asyncio.sleep(1)
    
    print("\n" + "="*50)
    print(f"Resumen de pruebas:")
    print(f"- Total proxies probados: {len(proxies)}")
    print(f"- Proxies funcionando: {working_count}")
    print(f"- Tasa de éxito: {working_count/len(proxies)*100:.1f}%")
    
    if save_working and working_count > 0:
        print(f"\nLos proxies que funcionan se han guardado en: {working_proxies_path}")
    
    # Si hay al menos un proxy que funciona, guárdalo como el proxy predeterminado
    if working_count > 0:
        # Encontrar el primer proxy que funcionó
        for i, result in enumerate(results):
            if result is not None:
                default_proxy = proxies[i]
                with open("default_proxy.txt", 'w') as f:
                    f.write(default_proxy)
                print(f"\nSe ha guardado {default_proxy} como proxy predeterminado en: default_proxy.txt")
                break

async def main():
    print("=== PRUEBA DE PROXIES PARA YTS API ===")
    
    # Nombre del archivo con los proxies
    proxy_file = "proxies.txt"
    
    # Probar los proxies
    await test_proxies_from_file(proxy_file, max_concurrent=3)
    
    print("\n¡Prueba completada!")

if __name__ == "__main__":
    asyncio.run(main())