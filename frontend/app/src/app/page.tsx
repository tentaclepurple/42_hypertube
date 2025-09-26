"use client";

import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { Movie } from "./movies/types/movies";

export default function Home() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [scrollInterval, setScrollInterval] = useState<NodeJS.Timeout | null>(null);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    const fetchPublicMovies = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/search/public/list`);
        if (!response.ok) {
          throw new Error('Failed to fetch movies');
        }
        const data: Movie[] = await response.json();
        console.log(data);
        setMovies(data);
        if (data.length > 0) {
          setSelectedMovie(data[0]);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchPublicMovies();
  }, []);

  const handleMovieSelect = (movie: Movie, index: number) => {
    setSelectedMovie(movie);
  };

  const startScroll = (direction: "left" | "right") => {
    if (scrollInterval) return;
    const container = document.getElementById("movie-carousel");
    if (!container) return;
  
    const interval = setInterval(() => {
      container.scrollBy({
        left: direction === "left" ? -10 : 10,
        behavior: "smooth"
      });
    }, 30);
    setScrollInterval(interval);
  };
  
  const stopScroll = () => {
    if (scrollInterval) {
      clearInterval(scrollInterval);
      setScrollInterval(null);
    }
  };

  if (loading) {
    return (
      <main className="flex items-center justify-center py-20 bg-black">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-red-600"></div>
      </main>
    );
  }

  if (error || movies.length === 0) {
    return (
      <main className="flex flex-col items-center justify-center py-20 bg-black text-white">
        <h1 className="text-2xl font-bold mb-4">{error || 'No movies available'}</h1>
      </main>
    );
  }

  return (
    <main className="bg-black text-white fixed inset-0 top-16 bottom-16 flex flex-col overflow-hiddenbg-black text-white fixed inset-0 top-16 bottom-16 flex flex-col overflow-hidden">
      {selectedMovie && (
        <div className="relative flex-1 flex items-end justify-start overflow-hidden">
          <Image
            src={selectedMovie.poster || '/no-poster.png'}
            alt={selectedMovie.title}
            fill
            unoptimized
            className="object-cover blur-2xl scale-110 opacity-50" 
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>
          <div className="relative z-10 p-8 flex gap-6 items-end">
            <div className="relative w-36 sm:w-48 md:w-60 lg:w-72 aspect-[2/3] rounded-lg overflow-hidden shadow-2xl">
              <Image
                src={selectedMovie.poster || '/no-poster.png'}
                alt={selectedMovie.title}
                fill
                unoptimized
                className="object-cover"
              />
            </div>
            <div className="max-w-xl">
              <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-2">{selectedMovie.title}</h1>
              <p className="text-sm sm:text-base md:text-lg text-gray-300">{selectedMovie.year}</p>
            </div>
          </div>
        </div>
      )}
      <div className="relative px-4 md:px-6 py-4 flex-shrink-0 bg-black">
        <h2 className="text-lg md:text-xl font-bold mb-3">{t('main.popularMovies')}</h2>
        <button
          onMouseEnter={() => startScroll("left")}
          onMouseLeave={stopScroll}
          className="absolute left-2 top-1/2 z-10 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>

        <button
          onMouseEnter={() => startScroll("right")}
          onMouseLeave={stopScroll}
          className="absolute right-2 top-1/2 z-10 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
        <div
          id="movie-carousel"
          className="flex space-x-4 overflow-x-auto scrollbar-hide scroll-smooth"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {movies.map((movie, index) => (
            <div
              key={movie.id || movie.imdb_id}
              onClick={() => handleMovieSelect(movie, index)}
              className={`flex-shrink-0 cursor-pointer transition-transform duration-300 hover:scale-105 ${
                selectedMovie?.id === movie.id ? 'ring-2 ring-red-600' : ''
              }`}
            >
              <div className="w-32 h-48 md:w-40 md:h-60 relative rounded-lg overflow-hidden">
                <Image
                  src={movie.poster || '/no-poster.png'}
                  alt={movie.title}
                  fill
                  unoptimized
                  className="object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300">
                  <div className="absolute bottom-0 p-4">
                    <h3 className="text-sm font-semibold truncate">{movie.title}</h3>
                    <p className="text-xs text-gray-300">{movie.year}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
