"use client";

import { useState, useEffect, useRef } from "react";
import { Movie } from "./types/movies";
import Link from 'next/link';
import { useAuth } from "../context/authcontext";
import { parsedError } from "../ui/error/parsedError";
import { useTranslation } from 'react-i18next';
import { useMovieFilters } from "../ui/filters/useMovieFilters";
import { MovieFilters } from "../ui/filters/movieFilters";
import Image from "next/image";

export default function Movies() {
    const { logout } = useAuth();
    const [movies, setMovies] = useState<Movie[]>([]);
    const [filteredMovies, setFilteredMovies] = useState<Movie[]>([]);
    const [error, setError] = useState<string[] | null>(null);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const observerRef = useRef<HTMLDivElement | null>(null);
    const { t } = useTranslation();
    const {
        filters,
        showFilters,
        setShowFilters,
        buildQueryString,
        filterAndSortMovies,
        handleFilterChange,
        toggleGenre,
        clearAllFilters
    } = useMovieFilters()

    useEffect(() => {
        const filtered = filterAndSortMovies(movies);
        setFilteredMovies(filtered);
    }, [movies, filters, filterAndSortMovies]);
    
    useEffect(() => {
        const fetchMovies = async () => {
            if(!hasMore) return;
            setLoading(true);
            const token = localStorage.getItem('token');
            try
            {   
                const queryString = buildQueryString(page);
                const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/search/popular?${queryString}`,
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
    }, [page, hasMore, logout, buildQueryString]);

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
            <h1 className="text-4xl font-bold mb-6 text-center">{t("movies.pageTitle")}</h1>
            {error && (
                <div className="text-center mt-4 py-2">
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                        {error}
                    </div>
                </div>
            )}
        <MovieFilters
            filters={filters}
            showFilters={showFilters}
            onToggleFilters={() => setShowFilters(!showFilters)}
            onFilterChange={handleFilterChange}
            onToggleGenre={toggleGenre}
            onClearFilters={clearAllFilters}
        />
        <div className="grid grid-cols-2 xs:grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {filteredMovies.map((movie) => (
                <Link key={movie.imdb_id || movie.id} href={`/movies/${movie.id}`} passHref>
                    <div className="bg-gray-800 p-2 rounded-lg transition-transform hover:scale-105">
                        <div className="relative pb-[150%]">
                            <Image
                                src={movie.poster || '/no-poster.png'}
                                alt={movie.title}
                                className="absolute inset-0 w-full h-full object-cover rounded-md"
                                width={300}
                                height={450}
                                unoptimized
                                priority={false}
                                quality={75}
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
        {filteredMovies.length === 0 && !loading &&(
            <div className="text-center mt-4 py-2">
                <p>{t("movies.noMoviesFound")}</p>
            </div>
        )}
        <div ref={observerRef} className="h-10" /></div>
    );
}