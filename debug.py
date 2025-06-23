#!/usr/bin/env python3
# debug_hash_conversion.py

import re

def hash_to_magnet_simple(torrent_hash: str, movie_title: str = None) -> str:
    """
    Convierte un hash a magnet link de forma simple
    """
    # Limpiar el hash
    clean_hash = torrent_hash.strip().lower()
    
    # Validar formato del hash
    if not re.match(r'^[a-f0-9]{40}$', clean_hash):
        raise ValueError(f"Hash inválido: {torrent_hash}")
    
    print(f"✅ Hash válido: {clean_hash}")
    
    # Construir magnet link básico
    magnet = f"magnet:?xt=urn:btih:{clean_hash}"
    
    # Añadir título si se proporciona
    if movie_title:
        clean_title = re.sub(r'[^\w\s-]', '', movie_title).strip()
        clean_title = re.sub(r'[-\s]+', '+', clean_title)
        magnet += f"&dn={clean_title}"
    
    # Lista más amplia de trackers
    trackers = [
        'udp://tracker.openbittorrent.com:80/announce',
        'udp://tracker.opentrackr.org:1337/announce',
        'udp://9.rarbg.to:2710/announce',
        'udp://9.rarbg.me:2710/announce',
        'udp://tracker.leechers-paradise.org:6969/announce',
        'udp://exodus.desync.com:6969/announce',
        'udp://tracker.cyberia.is:6969/announce',
        'udp://open.stealth.si:80/announce',
        'udp://tracker.tiny-vps.com:6969/announce',
        'udp://retracker.lanta-net.ru:2710/announce',
        'udp://tracker.torrent.eu.org:451/announce',
        'udp://tracker.internetwarriors.net:1337/announce',
        'udp://bt1.archive.org:6969/announce',
        'udp://bt2.archive.org:6969/announce'
    ]
    
    # Añadir trackers
    for tracker in trackers:
        magnet += f"&tr={tracker}"
    
    return magnet

def test_hash_conversions():
    """Prueba conversiones de hashes conocidos"""
    
    # Hashes de prueba (algunos reales, algunos de ejemplo)
    test_hashes = [
        {
            'name': 'Big Buck Bunny',
            'hash': 'dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c',
            'description': 'Creative Commons movie'
        },
        {
            'name': 'Ubuntu ISO',
            'hash': '5E9A92A2F63C02AAE5B7F7C9F6A5B7F7C9F6A5B7',
            'description': 'Example hash'
        },
        {
            'name': 'Test Movie',
            'hash': 'c9e15763f722f23e98a29decdfae341b98d53056',
            'description': 'Another test'
        }
    ]
    
    print("🧪 Probando conversiones hash → magnet\n")
    
    for i, test in enumerate(test_hashes, 1):
        print(f"--- Test {i}: {test['name']} ---")
        print(f"Hash original: {test['hash']}")
        print(f"Descripción: {test['description']}")
        
        try:
            magnet = hash_to_magnet_simple(test['hash'], test['name'])
            print(f"✅ Magnet generado:")
            print(f"   {magnet[:100]}...")
            print(f"   Longitud total: {len(magnet)} caracteres")
            
            # Verificar componentes
            if 'xt=urn:btih:' in magnet:
                print(f"   ✅ Contiene info-hash")
            if '&dn=' in magnet:
                print(f"   ✅ Contiene display name")
            tracker_count = magnet.count('&tr=')
            print(f"   ✅ Trackers añadidos: {tracker_count}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

def validate_magnet(magnet_link: str) -> bool:
    """Valida que el magnet link sea correcto"""
    print(f"🔍 Validando magnet link...")
    
    if not magnet_link.startswith('magnet:?'):
        print(f"❌ No empieza con 'magnet:?'")
        return False
    
    if 'xt=urn:btih:' not in magnet_link:
        print(f"❌ No contiene 'xt=urn:btih:'")
        return False
    
    # Extraer hash
    hash_match = re.search(r'xt=urn:btih:([a-fA-F0-9]{40})', magnet_link)
    if not hash_match:
        print(f"❌ Hash no válido o no encontrado")
        return False
    
    hash_value = hash_match.group(1)
    print(f"✅ Hash extraído: {hash_value}")
    
    # Contar trackers
    tracker_count = magnet_link.count('&tr=')
    print(f"✅ Trackers encontrados: {tracker_count}")
    
    return True

if __name__ == "__main__":
    print("🔬 Debug de conversión Hash → Magnet\n")
    
    # Probar conversiones
    test_hash_conversions()
    
    print("=" * 50)
    print("\n🧲 Probando un magnet específico:")
    
    # Probar con un hash específico
    test_hash = 'dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c'
    test_title = 'Big Buck Bunny'
    
    try:
        magnet = hash_to_magnet_simple(test_hash, test_title)
        print(f"Hash: {test_hash}")
        print(f"Título: {test_title}")
        print(f"Magnet: {magnet}")
        print()
        
        # Validar el magnet generado
        is_valid = validate_magnet(magnet)
        print(f"¿Es válido? {'✅ SÍ' if is_valid else '❌ NO'}")
        
    except Exception as e:
        print(f"❌ Error generando magnet: {e}")