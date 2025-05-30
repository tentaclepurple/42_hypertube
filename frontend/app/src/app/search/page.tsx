"use client";

import { useState, useEffect, useRef } from "react";
import { Movie } from "../movies/types/movies";
import { Search as SearchIcon, X, Film, Filter, ChevronDown, SlidersHorizontal } from "lucide-react";
import Link from 'next/link';
import { useAuth } from "../context/authcontext";
import { parsedError } from "../ui/error/parsedError";

interface SearchFilters {
    query: string;
    yearFrom: string;
    yearTo: string;
    ratingFrom: string;
    ratingTo: string;
    sortBy: string;
    sortOrder: string;
}

export default function Search() {
    const { logout } = useAuth();
    const [allMovies, setAllMovies] = useState<Movie[]>([]);
    const [filteredMovies, setFilteredMovies] = useState<Movie[]>([]);
    const [error, setError] = useState<string[] | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedQuery, setDebounceQuery] = useState('');
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [initialSearch, setInitialSearch] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [limit, setLimit] = useState(20);
    const observerRef = useRef<HTMLDivElement | null>(null);

    const [filters, setFilters] = useState<SearchFilters>({
        query: '',
        yearFrom: '',
        yearTo: '',
        ratingFrom: '',
        ratingTo: '',
        sortBy: 'rating',
        sortOrder: 'desc'
    });

    const sortOptions = [
        { value: 'title', label: 'Title' },
        { value: 'year', label: 'Year' },
        { value: 'rating', label: 'Rating' },
        { value: 'view_percentage', label: 'Watch Progress' }
    ];

    const limitOptions = [10, 20, 30, 50];

    useEffect(() => {
        const filtered = filterAndSortMovies(allMovies);
        setFilteredMovies(filtered);
    }, [allMovies, filters]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebounceQuery(searchQuery);
            setFilters(prev => ({ ...prev, query: searchQuery }));
            if (searchQuery) {
                setInitialSearch(true);
                setPage(1);
                setAllMovies([]);
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const buildQueryString = (currentPage: number) => {
        const params = new URLSearchParams();
        
        if (filters.query.trim()) {
            params.append('query', filters.query.trim());
        }
        
        params.append('page', currentPage.toString());
        params.append('limit', limit.toString());
        
        return params.toString();
    };

    const filterAndSortMovies = (movieList: Movie[]) => {
        let filtered = [...movieList];

        if (filters.yearFrom) {
            filtered = filtered.filter(movie => movie.year >= parseInt(filters.yearFrom));
        }
        if (filters.yearTo) {
            filtered = filtered.filter(movie => movie.year <= parseInt(filters.yearTo));
        }

        if (filters.ratingFrom) {
            filtered = filtered.filter(movie => movie.rating >= parseFloat(filters.ratingFrom));
        }
        if (filters.ratingTo) {
            filtered = filtered.filter(movie => movie.rating <= parseFloat(filters.ratingTo));
        }

        filtered.sort((a, b) => {
            let aValue: any;
            let bValue: any;

            switch (filters.sortBy) {
                case 'title':
                    aValue = a.title.toLowerCase();
                    bValue = b.title.toLowerCase();
                    break;
                case 'year':
                    aValue = a.year;
                    bValue = b.year;
                    break;
                case 'rating':
                    aValue = a.rating;
                    bValue = b.rating;
                    break;
                case 'view_percentage':
                    aValue = a.view_percentage || 0;
                    bValue = b.view_percentage || 0;
                    break;
                default:
                    aValue = a.rating;
                    bValue = b.rating;
            }

            if (aValue < bValue) {
                return filters.sortOrder === 'asc' ? -1 : 1;
            }
            if (aValue > bValue) {
                return filters.sortOrder === 'asc' ? 1 : -1;
            }
            return 0;
        });

        return filtered;
    };

    useEffect(() => {
        if (!debouncedQuery && !hasActiveFilters()) return;
        
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
                    if (response.status === 401) logout();
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
                setHasMore(data.length === limit);
            } catch (err) {
                setHasMore(false);
                setError(err as string[]);
            } finally {
                setLoading(false);
            }
        };
        
        fetchMovies();
    }, [debouncedQuery, page, filters, limit]);

    useEffect(() => {
        if (!hasMore || loading) return;
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && hasMore && (debouncedQuery || hasActiveFilters())) {
                setPage((prevPage) => prevPage + 1);
            }
        }, { threshold: 1 });
        if (observerRef.current) observer.observe(observerRef.current);
        return () => observer.disconnect();
    }, [hasMore, loading, debouncedQuery, filters]);

    const hasActiveFilters = () => {
        return filters.yearFrom || filters.yearTo || 
               filters.ratingFrom || filters.ratingTo;
    };

    const handleFilterChange = (key: keyof SearchFilters, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const clearAllFilters = () => {
        setFilters({
            query: searchQuery,
            yearFrom: '',
            yearTo: '',
            ratingFrom: '',
            ratingTo: '',
            sortBy: 'title',
            sortOrder: 'asc'
        });
    };

    const renderContent = () => {
        if (filteredMovies.length === 0 && !loading && initialSearch) {
            return (
                <div className="text-center py-10">
                    <p className="text-xl text-gray-400">No movies found with current filters</p>
                </div>
            );
        }

        return (
            <div className="grid grid-cols-2 xs:grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {filteredMovies.map((movie) => (
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
        <div className="p-4 bg-dark-900 text-white min-h-screen">
            {/* Search Bar */}
            <div className="relative mb-4 max-w-2xl mx-auto">
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
            <div className="flex justify-center mb-6">
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                    <SlidersHorizontal className="h-4 w-4" />
                    Advanced Filters
                    <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
                </button>
            </div>
            {showFilters && (
                <div className="bg-gray-800 p-6 rounded-lg mb-6 max-w-4xl mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

                        <div>
                            <label className="block text-sm font-medium mb-2">Year From</label>
                            <input
                                type="number"
                                placeholder="e.g. 2000"
                                value={filters.yearFrom}
                                onChange={(e) => handleFilterChange('yearFrom', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                min="1900"
                                max={new Date().getFullYear()}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">Year To</label>
                            <input
                                type="number"
                                placeholder="e.g. 2024"
                                value={filters.yearTo}
                                onChange={(e) => handleFilterChange('yearTo', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                min="1900"
                                max={new Date().getFullYear()}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">Min Rating</label>
                            <input
                                type="number"
                                placeholder="e.g. 7.0"
                                value={filters.ratingFrom}
                                onChange={(e) => handleFilterChange('ratingFrom', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                min="0"
                                max="10"
                                step="0.1"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">Max Rating</label>
                            <input
                                type="number"
                                placeholder="e.g. 10.0"
                                value={filters.ratingTo}
                                onChange={(e) => handleFilterChange('ratingTo', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                min="0"
                                max="10"
                                step="0.1"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">Sort By</label>
                            <select
                                value={filters.sortBy}
                                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                {sortOptions.map(option => (
                                    <option key={option.value} value={option.value}>{option.label}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">Order</label>
                            <select
                                value={filters.sortOrder}
                                onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="asc">Ascending</option>
                                <option value="desc">Descending</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">Results per page</label>
                            <select
                                value={limit}
                                onChange={(e) => {
                                    setLimit(Number(e.target.value));
                                    setPage(1);
                                    setAllMovies([]);
                                }}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                {limitOptions.map(option => (
                                    <option key={option} value={option}>{option}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="mt-4 flex justify-end">
                        <button
                            onClick={clearAllFilters}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                        >
                            Clear All Filters
                        </button>
                    </div>
                </div>
            )}
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
                    <p className="text-xl text-gray-400">Search for movies or use filters to display results</p>
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