"use client";

import { useState, useEffect, useRef } from "react";
import { Movie } from "../movies/types/movies";
import Link from 'next/link';
import { useAuth } from "../context/authcontext";
import { parsedError } from "../ui/error/parsedError";
import { useTranslation } from 'react-i18next';

export default function FavoriteMovies() {
    const { logout } = useAuth();
    const [movies, setMovies] = useState<Movie[]>([]);
    const [error, setError] = useState<string[] | null>(null);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const observerRef = useRef<HTMLDivElement | null>(null);
    const { t } = useTranslation();
    
    useEffect(() => {
        const fetchMovies = async () => {
            if(!hasMore) return;
            setLoading(true);
            const token = localStorage.getItem('token');
            try
            {
                const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/user-activity/favorites?page=${page}&limit=10`, 
                {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
                );
                if(!response.ok){
                    if(response.status === 401) logout();
                    const errorText = parsedError(await response.json());
                    return Promise.reject(errorText);
                };
                const data: Movie[] = await response.json();
                setMovies((prevMovies) => {
                    const existingIds = new Set(prevMovies.map(m => m.imdb_id || m.id));
                    const newMovies = data.filter(movie => !existingIds.has(movie.imdb_id || movie.id));
                    return [...prevMovies, ...newMovies];
                });
                setHasMore(data.length > 0);
            }catch(err){
                setError(err as string[]);
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
        <div className="p-4 bg-dark-900 text-white">
            {error && (
                <div className="text-center mt-4 py-2">
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                        {error}
                    </div>
                </div>
            )}
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
                            {movie.completed && (
                                <span className="flex items-center gap-1 text-green-500">
                                    {t("movies.watched")}
                                </span>
                            )}
                            <span>⭐ {movie.rating}/10</span>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
        {loading && (
        <div className="text-center mt-4 py-2">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
            <p className="mt-2">{t("movies.loadingMore")}</p>
        </div>
        )}
        <div ref={observerRef} className="h-10" />
    </div>
    );       
  }