import React from "react";
import { ChevronDown, SlidersHorizontal } from "lucide-react";
import { useTranslation } from "react-i18next";
import { SearchFilters, GENRE_OPTIONS } from "./useMovieFilters";

interface MovieFiltersProps {
    filters: SearchFilters;
    showFilters: boolean;
    onToggleFilters: () => void;
    onFilterChange: (key: keyof SearchFilters, value: string | string[]) => void;
    onToggleGenre: (genreTag: string) => void;
    onClearFilters: () => void;
}

export const MovieFilters: React.FC<MovieFiltersProps> = ({
    filters,
    showFilters,
    onToggleFilters,
    onFilterChange,
    onToggleGenre,
    onClearFilters,
}) => {
    const { t } = useTranslation();

    const sortOptions = [
        { value: 'title', label: t("search.filter.sortOptions.title") },
        { value: 'year', label: t("search.filter.sortOptions.year") },
        { value: 'rating', label: t("search.filter.sortOptions.rating") },
        { value: 'view_percentage', label: t("search.filter.sortOptions.viewPercentage") },
        { value: 'hypertube_rating', label: t("search.filter.sortOptions.hypertube_rating") }
    ];

    const limitOptions = [10, 20, 30, 50];

    return (
        <>
            <div className="flex justify-center mb-6">
                <button
                    onClick={onToggleFilters}
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
                                onChange={(e) => onFilterChange('yearFrom', e.target.value)}
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
                                onChange={(e) => onFilterChange('yearTo', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                min="1900"
                                max={new Date().getFullYear()}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">{t("search.filter.sort")}</label>
                            <select
                                value={filters.sortBy}
                                onChange={(e) => onFilterChange('sortBy', e.target.value)}
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
                                onChange={(e) => onFilterChange('sortOrder', e.target.value)}
                                className="w-full p-2 bg-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="asc">{t("search.filter.order.asc")}</option>
                                <option value="desc">{t("search.filter.order.desc")}</option>
                            </select>
                        </div>
                    </div>
                    <div className="mt-6">
                        <label className="block text-sm font-medium mb-3 text-center">{t("search.filter.selectGenres")}</label>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                            {GENRE_OPTIONS.map((genre) => (
                                <button
                                    key={genre.tag}
                                    onClick={() => onToggleGenre(genre.tag)}
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
                            onClick={onClearFilters}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                        >
                            {t("search.filter.clear")}
                        </button>
                    </div>
                </div>
            )}
        </>
    )
};