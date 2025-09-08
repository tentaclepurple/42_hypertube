"use client";

import { useState, useEffect, useRef } from "react";
import { Movie } from "../movies/types/movies";
import { Search as SearchIcon, X, Film, ChevronDown, SlidersHorizontal } from "lucide-react";
import Link from 'next/link';
import { useAuth } from "../context/authcontext";
import { parsedError } from "../ui/error/parsedError";
import { useTranslation } from "react-i18next";

interface SearchFilters {
    query: string;
    yearFrom: string;
    yearTo: string;
    ratingFrom: string;
    ratingTo: string;
    sortBy: string;
    sortOrder: string;
    genres: string[];
}

const GENRE_OPTIONS = [
    {tag: 'Action', key: 'search.filter.genres.action'},
    {tag: 'Adventure', key: 'search.filter.genres.adventure'},
    {tag: 'Animation', key: 'search.filter.genres.animation'},
    {tag: 'Documentary', key: 'search.filter.genres.documentary'},
    {tag: 'Comedy', key: 'search.filter.genres.comedy'},
    {tag: 'Crime', key: 'search.filter.genres.crime'},
    {tag: 'Drama', key: 'search.filter.genres.drama'},
    {tag: 'Family', key: 'search.filter.genres.family'},
    {tag: 'Fantasy', key: 'search.filter.genres.fantasy'},
    {tag: 'Horror', key: 'search.filter.genres.horror'},
    {tag: 'History', key: 'search.filter.genres.history'},
    {tag: 'Mystery', key: 'search.filter.genres.mystery'},
    {tag: 'Musical', key: 'search.filter.genres.musical'},
    {tag: 'Romance', key: 'search.filter.genres.romance'},
    {tag: 'Sci-Fi', key: 'search.filter.genres.scifi'},
    {tag: 'Thriller', key: 'search.filter.genres.thriller'},
    {tag: 'Western', key: 'search.filter.genres.western'},
    {tag: 'War', key: 'search.filter.genres.war'},
];

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
    const [isLoggingOut, setIsLoggingOut] = useState(false);
    const { t } = useTranslation();

    const [filters, setFilters] = useState<SearchFilters>({
        query: '',
        yearFrom: '',
        yearTo: '',
        ratingFrom: '',
        ratingTo: '',
        sortBy: 'rating',
        sortOrder: 'desc',
        genres: []
    });

    const sortOptions = [
        { value: 'title', label: t("search.filter.sortOptions.title") },
        { value: 'year', label: t("search.filter.sortOptions.year") },
        { value: 'rating', label: t("search.filter.sortOptions.rating") },
        { value: 'view_percentage', label: t("search.filter.sortOptions.viewPercentage") }
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

        if (filters.genres.length > 0) {
            filters.genres.forEach(genre => {
                params.append('genres', genre);
            });
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

        if (filters.genres.length > 0) {
            filtered = filtered.filter(movie => {
                const movieGenresLower = movie.genres.map(g => g.toLowerCase());
                return filters.genres.every(selectedGenre =>
                    movieGenresLower.includes(selectedGenre.toLowerCase())
                );
            });
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
                console.log("Fetched movies:", data);
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
        if (!hasMore || loading || isLoggingOut) return;
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
               filters.ratingFrom || filters.ratingTo ||
               filters.genres.length > 0;
    };

    const handleFilterChange = (key: keyof SearchFilters, value: string | string[]) => {
        setFilters(prev => ({ ...prev, [key]: value }));
        if (key === 'genres') {
            setPage(1);
            setAllMovies([]);
        }
    };

    const toggleGenre = (genreTag: string) => {
        const newGenres = filters.genres.includes(genreTag)
            ? filters.genres.filter(g => g !== genreTag)
            : [...filters.genres, genreTag];
        
        handleFilterChange('genres', newGenres);
    };
    const clearAllFilters = () => {
        setFilters({
            query: searchQuery,
            yearFrom: '',
            yearTo: '',
            ratingFrom: '',
            ratingTo: '',
            sortBy: 'rating',
            sortOrder: 'desc',
            genres: []
        });
    };

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
        );
    };

    return (
        <div className="p-4 bg-dark-900 text-white">
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
            <div className="flex justify-center mb-6">
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                    <SlidersHorizontal className="h-4 w-4" />
                        {t("search.filter.advanced")}
                    <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
                </button>
            </div>
            {showFilters && (
                <div className="bg-gray-800 p-6 rounded-lg mb-6 max-w-4xl mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">{t("search.filter.yearFrom")}</label>
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
                            <label className="block text-sm font-medium mb-2">{t("search.filter.yearTo")}</label>
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
                            <label className="block text-sm font-medium mb-2">{t("search.filter.minRating")}</label>
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
                            <label className="block text-sm font-medium mb-2">{t("search.filter.maxRating")}</label>
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
                            <label className="block text-sm font-medium mb-2">{t("search.filter.sort")}</label>
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
                            <label className="block text-sm font-medium mb-2">{t("search.filter.order.orderBy")}</label>
                            <select
                                value={filters.sortOrder}
                                onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="asc">{t("search.filter.order.asc")}</option>
                                <option value="desc">{t("search.filter.order.desc")}</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">{t("search.filter.resultsPerPage")}</label>
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
                    <div className="mt-6">
                        <label className="block text-sm font-medium mb-3 text-center">{t("search.filter.selectGenres")}</label>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                            {GENRE_OPTIONS.map((genre) => (
                                <button
                                    key={genre.tag}
                                    onClick={() => toggleGenre(genre.tag)}
                                    className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                                        filters.genres.includes(genre.tag)
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                    }`}
                                >
                                    {t(genre.key)}
                                </button>
                            ))}
                        </div>
                    </div>                   
                    <div className="mt-4 flex justify-end">
                        <button
                            onClick={clearAllFilters}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                        >
                            {t("search.filter.clear")}
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