"use client";

import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { Movie } from "./movies/types/movies";
import { useRouter } from "next/navigation";

export default function Home() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [scrollInterval, setScrollInterval] = useState<NodeJS.Timeout | null>(null);
  const { t } = useTranslation();
  const router = useRouter();

  useEffect(() => {
    const fetchPublicMovies = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/search/public/list`);
        if (!response.ok) throw new Error("Failed to fetch movies");
        const data: Movie[] = await response.json();
        setMovies(data);
        if (data.length > 0) setSelectedMovie(data[0]);
      } catch (err) {
        console.error(err);
      }
    };
    fetchPublicMovies();
  }, []);


  const startScroll = (direction: "left" | "right") => {
    if (scrollInterval) return;
    const container = document.getElementById("movie-carousel");
    if (!container) return;

    const interval = setInterval(() => {
      container.scrollBy({ left: direction === "left" ? -10 : 10, behavior: "smooth" });
    }, 30);

    setScrollInterval(interval);
  };

  const stopScroll = () => {
    if (scrollInterval) {
      clearInterval(scrollInterval);
      setScrollInterval(null);
    }
  };

  const handleMovieClick = (movie: Movie) => {
    if (selectedMovie?.id === movie.id) {
      window.location.href = `/movies/${movie.id}`;
    } else {
      setSelectedMovie(movie);
    }
  };

  return (
    <main className="bg-black text-white fixed inset-0 top-16 bottom-16 flex flex-col overflow-auto lg:overflow-hidden">
      {selectedMovie && (
        <div className="relative flex-1 flex flex-col lg:flex-row items-center lg:items-end justify-center lg:justify-start overflow-hidden">
          <Image
            src={selectedMovie.poster || "/no-poster.png"}
            alt={selectedMovie.title}
            fill
            unoptimized
            className="object-cover blur-2xl scale-110 opacity-50"
            priority
          />
          <div className="relative z-10 w-full flex flex-col lg:hidden items-center gap-3 p-4 sm:p-6">
            <div
              className="relative w-40 sm:w-48 aspect-[2/3] rounded-lg overflow-hidden shadow-2xl cursor-pointer"
              onClick={() => router.push(`/movies/${selectedMovie.id}`)}
            >
              <Image
                src={selectedMovie.poster || "/no-poster.png"}
                alt={selectedMovie.title}
                fill
                unoptimized
                className="object-cover"
              />
            </div>
            <div
              className="text-center max-w-xs sm:max-w-md"
              onClick={() => router.push(`/movies/${selectedMovie.id}`)}
            >
              <h1 className="text-base sm:text-xl font-bold leading-tight">
                {selectedMovie.title}
              </h1>
              <p className="text-xs sm:text-sm text-gray-300">{selectedMovie.year}</p>
            </div>
          </div>
          <div className="relative z-10 hidden lg:flex gap-6 p-4 md:p-6 lg:p-8 items-end">
            <div
              className="relative rounded-lg overflow-hidden shadow-2xl cursor-pointer w-[25vw] md:w-[20vw] lg:w-[18vw] max-w-[280px] aspect-[2/3]"
              onClick={() => router.push(`/movies/${selectedMovie.id}`)}
            >
              <Image
                src={selectedMovie.poster || "/no-poster.png"}
                alt={selectedMovie.title}
                fill
                unoptimized
                className="object-cover"
              />
            </div>
            <div
              className="max-w-[50vw] cursor-pointer"
              onClick={() => router.push(`/movies/${selectedMovie.id}`)}
            >
              <h1 className="font-bold mb-2 leading-tight text-[2.5vw] md:text-[2vw] lg:text-5xl">
                {selectedMovie.title}
              </h1>
              <p className="text-gray-300 text-[1.2vw] md:text-[1vw] lg:text-lg">{selectedMovie.year}</p>
            </div>
          </div>
        </div>
      )}
      <div className="relative px-4 md:px-6 py-4 flex-shrink-0 bg-black flex-1 flex flex-col justify-center lg:flex-none lg:justify-start">
        <h2 className="relative z-10 text-lg md:text-xl font-bold mb-3">
          {t("main.popularMovies")}
        </h2>
        <button
          onMouseEnter={() => startScroll("left")}
          onMouseLeave={stopScroll}
          className="hidden md:block absolute left-2 top-1/2 z-20 -translate-y-1/2 bg-black/80 hover:bg-black/90 text-white p-3 rounded-full shadow-lg transition"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>
        <button
          onMouseEnter={() => startScroll("right")}
          onMouseLeave={stopScroll}
          className="hidden md:block absolute right-2 top-1/2 z-20 -translate-y-1/2 bg-black/80 hover:bg-black/90 text-white p-3 rounded-full shadow-lg transition"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
        <div
          id="movie-carousel"
          className="relative z-10 flex space-x-4 overflow-x-auto md:overflow-x-auto scrollbar-hide scroll-smooth"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          {movies.map((movie) => (
            <div
              key={movie.id || movie.imdb_id}
              onClick={() => handleMovieClick(movie)}
              className={`flex-shrink-0 cursor-pointer transition-transform duration-300 hover:scale-105 ${
                selectedMovie?.id === movie.id ? "ring-2 ring-red-600" : ""
              }`}
            >
              <div className="w-[30vw] sm:w-[22vw] md:w-[18vw] lg:w-[12vw] max-w-[160px] aspect-[2/3] rounded-lg overflow-hidden relative group">
                <Image
                  src={movie.poster || "/no-poster.png"}
                  alt={movie.title}
                  fill
                  unoptimized
                  className="object-cover"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="p-2 sm:p-3">
                    <h3 className="text-xs sm:text-sm font-semibold line-clamp-2 sm:line-clamp-3 break-words">
                      {movie.title}
                    </h3>
                    <p className="text-[10px] sm:text-xs text-gray-300">{movie.year}</p>
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
