┌───────────────────────────────────────────────────────────────────┐
│                           CLIENTE WEB                             │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │  Login/  │  │Biblioteca│  │Reproductor│  │  Perfil Usuario  │  │
│  │ Registro │  │y Búsqueda│  │  Video    │  │                  │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └──────────────────┘  │
└───────┼──────────────┼──────────────┼─────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
┌───────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (FastAPI)                     │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐            │
│  │Auth/Users│ │ Búsqueda │ │   Video   │ │ REST API  │            │
│  │Module    │ │ Module   │ │  Module   │ │ Module    │            │
│  └────┬─────┘ └───┬──────┘ └────┬──────┘ └─────┬─────┘            │
└───────┼───────────┼─────────────┼─────────────┼───────────────────┘
        │           │             │             │
        ▼           │             │             │
  ┌───────────┐     │             │             │
  │ Supabase  │◄────┘             │             │
  │ Auth &    │◄─────────────────┐│             │
  │ Database  │                  ││             │
  └─────┬─────┘                  ││             │
        │           ┌────────────┘│             │
        │           │             │             │
        ▼           ▼             ▼             ▼
┌──────────────────────────────────────────────────────────────────┐
│                          KAFKA                                   │
│ ┌─────────────┐ ┌───────────-─┐ ┌──────────────┐ ┌────────────┐  │
│ │user-events  │ │video-request│ │torrent-status│ │recommend-  │  │
│ │   topic     │ │   topic     │ │    topic     │ │   topic    │  │
│ └──────┬──────┘ └──────┬──────┘ └─────┬────────┘ └─────┬──────┘  │
└────────┼─────────────┬─┴────────────┬─┴────────────────┼─────────┘
         │             │              │                  │
         ▼             ▼              ▼                  ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐
│  Servicio   │ │  Servicio    │ │  Servicio    │ │   Servicio     │
│    de       │ │     de       │ │     de       │ │      de        │
│  Eventos    │ │   Torrents   │ │  Conversión  │ │ Recomendación  │
└─────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬─────────┘
      │                │                │                │
      └────────────┐   │                │                │
                   ▼   ▼                ▼                ▼
           ┌─────────────────────────────────────────────┐
           │                                             │
           │          Almacenamiento                     │
           │  ┌─────────────┐  ┌────────────────┐        │
           │  │PostgreSQL DB│  │Sistema Archivos│        │
           │  │(+pgvector)  │  │(Videos/Images) │        │
           │  └─────────────┘  └────────────────┘        │
           │                                             │
           └─────────────────────────────────────────────┘


---


# Flujos Principales de Datos

## 1. Flujo de Autenticación de Usuario
Usuario → Login/Registro UI → API Gateway → Supabase Auth → 
Kafka (user-events) → Base de datos → API Gateway → Usuario

## 2. Flujo de Búsqueda y Biblioteca
Usuario → Búsqueda UI → API Gateway → Supabase/APIs externas → 
Resultados filtrados → (Opcional: evento Kafka) → Usuario

## 3. Flujo de Solicitud y Reproducción de Video
Usuario → Selecciona Video → API Gateway → 
Kafka (video-request) → Servicio de Torrents → 
Descarga Torrent → Kafka (torrent-status) → 
Servicio de Streaming/Conversión → Almacenamiento → 
API Gateway → Reproductor → Usuario

## 4. Flujo de Recomendaciones
Usuario → Interacciones → API Gateway → Kafka (user-events) → 
Servicio de Recomendaciones → pgvector (búsqueda) → 
Resultados recomendados → API Gateway → UI → Usuario


---


# Desglose de Componentes Clave


## 1. Frontend (Cliente Web)

Interfaz de Usuario: Páginas de login, registro, biblioteca, reproductor, perfil
Estado de Cliente: Gestión de sesión, preferencias, historial
Comunicación: API REST + WebSockets para actualizaciones en tiempo real


## 2. API Gateway (FastAPI)

Gestión de rutas: Endpoints para todas las funcionalidades
Middleware: Autenticación, validación, logging
Módulos: Usuarios, videos, búsqueda, API REST pública


## 3. Supabase (PostgreSQL + Servicios)

Autenticación: OAuth con 42 y otros proveedores
Base de Datos Relacional: Usuarios, películas, comentarios, historial
pgvector: Búsqueda vectorial para recomendaciones
Storage: Almacenamiento de imágenes y datos pequeños


## 4. Kafka (Bus de Mensajes)

Topics clave:

user-events: Actividad de usuario para analítica y recomendaciones
video-request: Solicitudes para iniciar descargas de torrents
torrent-status: Progreso de descargas
conversion-events: Estado de conversión de videos
recommendation-events: Eventos para recomendaciones



## 5. Servicios de Backend

Servicio de Torrents: Descarga y gestión de archivos de video
Servicio de Conversión: Transformación de formatos no compatibles
Servicio de Streaming: Entrega de contenido al cliente
Servicio de Subtítulos: Obtención y gestión de subtítulos
Servicio de Recomendaciones: Generación de recomendaciones personalizadas


## 6. Almacenamiento

PostgreSQL: Datos relacionales y vectores (con pgvector)
Sistema de Archivos: Videos descargados y procesados
Caché (Redis): Mejora de rendimiento para consultas frecuentes


# Ciclo de Vida de un Video en Hypertube

Descubrimiento: Usuario encuentra un video por búsqueda o recomendación
Solicitud: Usuario solicita ver el video
Descarga: Sistema verifica si existe localmente; si no, inicia descarga por torrent
Streaming Temprano: Cuando hay suficiente buffer, comienza el streaming
Conversión (si es necesario): Conversión al vuelo para formatos incompatibles
Almacenamiento: Una vez descargado completamente, se guarda
Caducidad: Si no es visto en un mes, se elimina
Analítica: Las interacciones alimentan el sistema de recomendaciones