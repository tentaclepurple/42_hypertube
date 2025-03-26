"use client";

import { useState, useEffect, useRef } from "react";
import { Movie } from "./types/movies";
import Link from 'next/link';
import { useAuth } from "../context/authcontext";

export default function Movies() {
    const { logout } = useAuth();
    const [movies, setMovies] = useState<Movie[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const observerRef = useRef<HTMLDivElement | null>(null);
    
    useEffect(() => {
        const fetchMovies = async () => {
            if(!hasMore) return;
            setLoading(true);
            const token = localStorage.getItem('authToken');
            try
            {
                const response = await fetch(`http://localhost:8000/api/v1/search/popular?page=${page}&limit=10`, 
                {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
                );
                if(!response.ok){
                    if(response.status === 401) logout();
                    const errorText = await response.text();
                    console.log(`Server error: Status ${response.status}, ${errorText}`);
                    setError(errorText);
                    return Promise.reject(errorText);
                };
                const data: Movie[] = await response.json();
                setMovies((prevMovies) => {
                    // Crear un conjunto de IDs existentes
                    const existingIds = new Set(prevMovies.map(m => m.imdb_id || m.id));
                    // Filtrar películas nuevas que no existan ya
                    const newMovies = data.filter(movie => !existingIds.has(movie.imdb_id || movie.id));
                    return [...prevMovies, ...newMovies];
                });
                setHasMore(data.length > 0);
            }catch(err){
                console.log('Error fetching movies:', err);
            }finally{
                setLoading(false);
            }
        };
        fetchMovies();
    }, [page]);

    useEffect(() => {
        const observer = new IntersectionObserver((entries) => {
            if(entries[0].isIntersecting && hasMore){
                setPage((prevPage) => prevPage + 1);
            }
        }, {threshold: 1});
        if(observerRef.current) observer.observe(observerRef.current);
        return () => observer.disconnect();
    }, [hasMore]);

    return (
        <div className="p-4 bg-dark-900 text-white min-h-screen">
            <h1 className="text-3xl font-bold mb-6">Popular Movies</h1>
            {error && (
                <div className="text-center mt-4 py-2">
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                        {error}
                    </div>
                </div>
            )}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {movies.map((movie) => (
                <Link key={movie.imdb_id || movie.id} href={`/movies/${movie.id}`} passHref>
                    <div key={movie.id} className="bg-gray-800 p-2 rounded-lg">
                        <img src={movie.poster} alt={movie.title} className="w-full h-64 object-cover rounded-md" />
                        <h2 className="text-lg font-bold mt-2 truncate">{movie.title}</h2>
                        <div className="flex justify-between text-sm text-gray-400">
                            <span>{movie.year}</span>
                            <span>⭐ {movie.rating}/10</span>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
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