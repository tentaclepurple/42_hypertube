"use client";

import { useState, useEffect, useRef, use } from "react";
import { Movie } from "../movies/types/movies";
import { Search as SearchIcon, X, Film } from "lucide-react";
import Link from 'next/link';
import { useAuth } from "../context/authcontext";
import { parsedError } from "../ui/error/parsedError";

export default function Search() {
    const { logout } = useAuth();
    const [movies, setMovies] = useState<Movie[]>([]);
    const [error, setError] = useState<string[] | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedQuery, setDebounceQuery] = useState('');
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [initialSearch, setInitialSearch] = useState(false);
    const observerRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebounceQuery(searchQuery);
            if (searchQuery){
                setInitialSearch(true);
                setPage(1);
                setMovies([]);
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    // Effect for movie search
    useEffect(() => {
        if(!debouncedQuery) return;
        const fetchMovies = async () => {
            setLoading(true);
            const token = localStorage.getItem('token');
            try{
                const response = await fetch(`http://localhost:8000/api/v1/search/movies?query=${encodeURIComponent(debouncedQuery)}&page=${page}`, {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                if(!response.ok) {
                    if(response.status === 401) logout();
                    const errorText = parsedError(await response.json());
                    return Promise.reject(errorText);
                }
                const data: Movie[] = await response.json();
                if (page === 1){
                    setMovies(data);
                } else {
                    setMovies((prevMovies) => {
                        // Crear un conjunto de IDs existentes
                        const existingIds = new Set(prevMovies.map(m => m.imdb_id || m.id));
                        // Filtrar películas nuevas que no existan ya
                        const newMovies = data.filter(movie => !existingIds.has(movie.imdb_id || movie.id));
                        return [...prevMovies, ...newMovies];
                    });
                }
                setHasMore(data.length === 20); // Si la respuesta tiene 20 películas, hay más por cargar
            } catch(err){
                setHasMore(false);
                setError(err as string[]);
            } finally{
                setLoading(false);
            }
        };
        fetchMovies();
    }, [debouncedQuery, page]);

    useEffect(() => {
        if(!hasMore || loading) return;
        const observer = new IntersectionObserver((entries) => {
            if(entries[0].isIntersecting && hasMore && debouncedQuery){
                setPage((prevPage) => prevPage + 1);
            }
        }, {threshold: 1});
        if(observerRef.current) observer.observe(observerRef.current);
        return () => observer.disconnect();
    }, [hasMore, loading, debouncedQuery]);

     // Función para renderizar el contenido de la página
    const renderContent = () => {
        if(movies.length === 0 && !loading && initialSearch){
            return (        
                <div className="text-center py-10">
                    <p className="text-xl text-gray-400">No movies found for “{debouncedQuery}”</p>
                </div>
            );
        }

        return (
            <div className="grid grid-cols-2 xs:grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {movies.map((movie) => (
                    <Link key={movie.imdb_id || movie.id} href={`/movies/${movie.id}`} passHref>
                        <div className="bg-gray-800 p-2 rounded-lg transition-transform hover:scale-105">
                            <div className="relative pb-[150%]">
                                <img
                                    src={movie.poster || '/no-poster.png'}
                                    alt={movie.title}
                                    className="absolute inset-0 w-full h-full object-cover rounded-md"
                                    onError={(e) => {
                                        e.currentTarget.src = '/no-poster.png';
                                    }}
                                />
                            </div>
                            <h2 className="text-lg font-bold mt-2 truncate">{movie.title}</h2>
                            <div className="flex justify-between text-sm text-gray-400">
                                <span>{movie.year}</span>
                                <span>⭐ {movie.rating}/10</span>
                            </div>
                        </div>
                    </Link>
                ))}
            </div>
        );
    };

    return (
        <div className="p-4 bg-dark-900 text-white">
            <div className="relative mb-8 max-w-2xl mx-auto">
                <input
                    type="text"
                    id="search"
                    name="search"
                    placeholder="Search movies..."
                    className="w-full p-4 pl-12 pr-4 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    autoComplete="off"
                />
                <SearchIcon className="h-6 w-6 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                {searchQuery && (
                    <button
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                        onClick={() => setSearchQuery('')}
                    >
                        <X className="h-5 w-5" />
                    </button>
                )}
            </div>
            { error && (
                <div className="text-center mt-4 py-2">
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                        {error}
                    </div>
                </div>
            )}
            {!initialSearch && !loading && movies.length === 0 && (
                    <div className="text-center py-10">
                        <Film className="h-16 w-16 mx-auto text-gray-600 mb-4" />
                        <p className="text-xl text-gray-400">Search for movies to display here</p>
                    </div>
            )}
            {renderContent()}
            {loading && (
                <div className="text-center mt-4 py-2">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
                    <p className="mt-2">Loading more movies...</p>
                </div>
            )}
            <div ref={observerRef} className="h-10" />
        </div>
    );
  }