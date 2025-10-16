"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { Movie } from "../movies/types/movies";
import { Search as SearchIcon, X, Film } from "lucide-react";
import Link from 'next/link';
import { useAuth } from "../context/authcontext";
import { parsedError } from "../ui/error/parsedError";
import { useTranslation } from "react-i18next";
import { useMovieFilters } from "../ui/filters/useMovieFilters";
import { MovieFilters } from "../ui/filters/movieFilters";
import Image from "next/image";

export default function Search() {
    const { logout } = useAuth();
    const [allMovies, setAllMovies] = useState<Movie[]>([]);
    const [filteredMovies, setFilteredMovies] = useState<Movie[]>([]);
    const [error, setError] = useState<string[] | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedQuery, setDebouncedQuery] = useState('');
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [initialSearch, setInitialSearch] = useState(false);
    const observerRef = useRef<HTMLDivElement | null>(null);
    const [isLoggingOut, setIsLoggingOut] = useState(false);
    const { t } = useTranslation();
    const {
        filters,
        showFilters,
        setShowFilters,
        filterAndSortMovies,
        buildQueryString,
        hasActiveFilters,
        handleFilterChange,
        toggleGenre,
        clearAllFilters,
        updateQuery
    } = useMovieFilters();
    const serializedFilters = useMemo(() => JSON.stringify(filters), [filters]);


    useEffect(() => {
        const filtered = filterAndSortMovies(allMovies);
        setFilteredMovies(filtered);
    }, [allMovies, filters, filterAndSortMovies]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedQuery(searchQuery);
            updateQuery(searchQuery);
            if (searchQuery) {
                setInitialSearch(true);
                setPage(1);
                setAllMovies([]);
                setHasMore(true);
                setError(null);  
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [searchQuery, updateQuery]);


    useEffect(() => {
        if ( isLoggingOut ||(!debouncedQuery && !hasActiveFilters())) return;
        const fetchMovies = async () => {
            setLoading(true);
            const token = localStorage.getItem('token');
            try {
                const queryString = buildQueryString(page);
                const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/search/movies?${queryString}`, {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                
                if (!response.ok) {
                    if (response.status === 401) {
                        setIsLoggingOut(true);
                        logout();
                    }
                    const errorText = parsedError(await response.json());
                    return Promise.reject(errorText);
                }
                
                const data: Movie[] = await response.json();
                if (page === 1) {
                    setAllMovies(data);
                } else {
                    setAllMovies((prevMovies) => {
                        const existingIds = new Set(prevMovies.map(m => m.imdb_id || m.id));
                        const newMovies = data.filter(movie => !existingIds.has(movie.imdb_id || movie.id));
                        return [...prevMovies, ...newMovies];
                    });
                }
                setHasMore(data.length > 0);
                setError(null);
            } catch (err) {
                setHasMore(false);
                setError(err as string[]);
            } finally {
                setLoading(false);
            }
        };
        
        fetchMovies();
    }, [debouncedQuery, page, serializedFilters, logout, buildQueryString, isLoggingOut, hasActiveFilters]);

    useEffect(() => {
        const observer = new IntersectionObserver((entries) => {
          if (entries[0].isIntersecting && hasMore && !loading && debouncedQuery) {
                setPage(prevPage => prevPage + 1);
          }
        }, { threshold: 1 });

        const currentRef = observerRef.current;
        if (currentRef) {
          observer.observe(currentRef);
        }
        return () => {
          if (currentRef) {
            observer.unobserve(currentRef);
          }
        };
      }, [hasMore, debouncedQuery, loading]);

    const renderContent = () => {
        if (filteredMovies.length === 0 && !loading && initialSearch) {
            return (
                <div className="text-center py-10">
                    <p className="text-xl text-gray-400">{t("search.noResults")}</p>
                </div>
            );
        }

        return (
            <div className="grid grid-cols-2 xs:grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {filteredMovies.map((movie) => (
                    <Link key={movie.imdb_id || movie.id} href={`/movies/${movie.id}`} passHref>
                        <div className="bg-gray-800 p-2 rounded-lg transition-transform hover:scale-105">
                            <div className="relative pb-[150%]">
                                <Image
                                    src={movie.poster || '/no-poster.png'}
                                    alt={movie.title}
                                    width={300}
                                    height={450}
                                    className="absolute inset-0 w-full h-full object-cover rounded-md"
                                    unoptimized
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
        );
    };

    return (
        <div className="p-4 bg-dark-900 text-white">
            <h1 className="text-4xl font-bold mb-6 text-center">{t("search.pageTitle")}</h1>
            <div className="relative mb-4 max-w-2xl mx-auto">
                <input
                    type="text"
                    id="search"
                    name="search"
                    placeholder={t("search.searchPlaceholder")}
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
            <MovieFilters
                filters={filters}
                showFilters={showFilters}
                onToggleFilters={() => setShowFilters(!showFilters)}
                onFilterChange={handleFilterChange}
                onToggleGenre={toggleGenre}
                onClearFilters={clearAllFilters}
            />
            {error && (
                <div className="text-center mt-4 py-2">
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                        {error}
                    </div>
                </div>
            )}
            {!initialSearch && !loading && filteredMovies.length === 0 && (
                <div className="text-center py-10">
                    <Film className="h-16 w-16 mx-auto text-gray-600 mb-4" />
                    <p className="text-xl text-gray-400">{t("search.search")}</p>
                </div>
            )}
            {renderContent()}
            {loading && (
                <div className="text-center mt-4 py-2">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
                    <p className="mt-2">{t("search.loading")}</p>
                </div>
            )}
            <div ref={observerRef} className="h-10" />
        </div>
    );
}