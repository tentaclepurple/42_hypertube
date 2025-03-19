"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation"; 
import { Movie } from "../types/movies";


export default function MovieDetails() {
    const { id } = useParams();
    const [movie, setMovie] = useState<Movie | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) return;
        const token = localStorage.getItem("token");
        fetch(`http://localhost:8000/api/v1/movies/${id}`, 
        {
            method: "GET",
            headers: { 
                Authorization: `Bearer ${token}` 
            },
        })
        .then((response) => response.json())
        .then((data) => {
            setMovie(data);
            setLoading(false);
        })
        .catch((err) => {
            console.error("Error fetching movie details:", err);
        });
    }, [id]);

    if (loading) return (
        <div className="text-center mt-4 py-2">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
            <p className="mt-2">Loading movie...</p>
        </div>
    );

    return (
        <div className="p-4 bg-dark-900 text-white min-h-screen">
            <div className="max-w-4xl mx-auto mx-auto flex flex-col md:flex-row">
                <img src={movie?.poster} alt={movie?.title} className="w-full md:w-auto max-w-xs sm:max-w-sm md:max-w-md h-auto rounded-lg mb-4 md:mb-0 md:mr-6" />
                <div>
                    <h1 className="text-4xl font-bold">{movie?.title}</h1>
                    <p className="text-gray-400">{movie?.runtime ?? "N/A"} • {movie?.year ?? "N/A"} • {movie?.rating ?? "N/A"}/10⭐ </p>
                    <p className="text-lg mt-4">{movie?.summary}</p>

                    <h3 className="mt-6 text-xl font-semibold">Director</h3>
                    <p>{movie?.director?.length? movie.director.join(", ") : "No director available"}</p>

                    <h3 className="mt-6 text-xl font-semibold">Cast</h3>
                    <p>{movie?.cast?.length? movie.cast.join(", ") : "No cast available"}</p>
                    <h3 className="text-2xl mt-8">Genres</h3>
                    <ul className="flex space-x-4">
                        {movie?.genres.map((genre) => (
                            <li key={genre} className="bg-gray-800 px-2 py-1 rounded-lg">{genre}</li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
}