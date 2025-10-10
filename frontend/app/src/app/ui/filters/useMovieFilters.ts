import { useState, useEffect } from "react";
import { Movie } from "../../movies/types/movies";


export interface SearchFilters {
    query: string;
    yearFrom: string;
    yearTo: string;
    sortBy: string;
    sortOrder: string;
    genres: string[];
}

export const GENRE_OPTIONS = [
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

interface UseMovieFiltersProps {
    initialquery?: string;
    onFiltersChange?: (filters: SearchFilters) => void;
}

export const useMovieFilters = ({ initialquery = "", onFiltersChange }: UseMovieFiltersProps = {}) => {
    const [filters, setFilters] = useState<SearchFilters>({
        query: initialquery,
        yearFrom: '',
        yearTo: '',
        sortBy: 'rating',
        sortOrder: 'desc',
        genres: []
    });

    const [showFilters, setShowFilters] = useState(false);

    useEffect(() => {
        onFiltersChange?.(filters);
    }, [filters, onFiltersChange]);

    const filterAndSortMovies = (movieList: Movie[]): Movie[] => {
        let filtered = [...movieList];

        if (filters.yearFrom) {
            filtered = filtered.filter(movie => movie.year >= parseInt(filters.yearFrom));
        }
        if (filters.yearTo) {
            filtered = filtered.filter(movie => movie.year <= parseInt(filters.yearTo));
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

    const buildQueryString = (currentPage: number): string => {
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

        return params.toString();
    };

    const hasActiveFilters = (): boolean => {
        return Boolean (
            filters.yearFrom || filters.yearTo ||
            filters.genres.length > 0
        );
    };

    const handleFilterChange = (key: keyof SearchFilters, value: string | string[]): void => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const toggleGenre = (genreTag: string): void => {
        const newGenres = filters.genres.includes(genreTag)
            ? filters.genres.filter(g => g !== genreTag)
            : [...filters.genres, genreTag];
        
        handleFilterChange('genres', newGenres);
    };

    const clearAllFilters = (): void => {
        setFilters({
            query: filters.query,
            yearFrom: '',
            yearTo: '',
            sortBy: 'rating',
            sortOrder: 'desc',
            genres: []
        });
    };

    const updateQuery = (query: string): void => {
        setFilters(prev => ({ ...prev, query}));
    };

    return {
        filters,
        setFilters,
        showFilters,
        setShowFilters,
        filterAndSortMovies,
        buildQueryString,
        hasActiveFilters,
        handleFilterChange,
        toggleGenre,
        clearAllFilters,
        updateQuery
    };

}