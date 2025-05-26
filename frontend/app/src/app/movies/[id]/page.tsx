"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Star, MessageCircle, Send } from "lucide-react";
import { Movie } from "../types/movies";
import { useAuth } from "../../context/authcontext";
import { parsedError } from "../../ui/error/parsedError";

interface Comment {
    id: string;
    comment: string;
    rating: number;
    username: string;
    createdAt: string;
}

export default function MovieDetails() {
    const { logout } = useAuth();
    const { id } = useParams();
    const [movieData, setMovieData] = useState<Movie | null>(null);
    const [error, setError] = useState<string[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [comments, setComments] = useState<Comment[]>([]);
    const [commentsloading, setCommentsLoading] = useState(false);
    const [newComment, setNewComment] = useState("");
    const [newRating, setNewRating] = useState(5);
    const [submitting, setSubmitting] = useState(false);


    const fectchMovieData = async () => {
        if (!id) return;
        const token = localStorage.getItem("token");
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/movies/${id}`, {
                method: "GET",
                headers: { 
                    Authorization: `Bearer ${token}` 
                },
            });
            if (!response.ok) {
                if (response.status === 401) logout();
                const text = parsedError(await response.json());
                return Promise.reject(text);
            }
            const data = await response.json();
            setMovieData(data);
        } catch (err) {
            setError(err as string[]);
        }
    };

    const fetchComments = async () => {
        if (!id) return;
        setCommentsLoading(true);
        const token = localStorage.getItem("token");
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/movies/${id}/comments`, {
                method: "GET",
                headers: { 
                    Authorization: `Bearer ${token}` 
                },
            });
            if (!response.ok) {
                if (response.status === 401) logout();
                const text = parsedError(await response.json());
                return Promise.reject(text);
            }
            const data = await response.json();
            setComments(data);
        } catch (err) {
            setError(err as string[]);
        } finally {
            setCommentsLoading(false);
        }
    };

    const submitComment = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newComment.trim() || !id) return;

        setSubmitting(true);
        const token = localStorage.getItem("token");
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/movies/${id}/comments`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    comment: newComment.trim(),
                    movieId: id as string,
                    rating: newRating,
                }),
            });
            if (!response.ok) {
                if (response.status === 401) logout();
                const text = parsedError(await response.json());
                return Promise.reject(text);
            }
            setNewComment("");
            setNewRating(5);
            await fetchComments();
        } catch (err) {
            setError(err as string[]);
        } finally {
            setSubmitting(false);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const renderStars = (rating: number) => {
        return Array.from({ length: 5 }, (_, index) => (
            <Star 
                key={index} 
                className={`h-4 w-4 ${
                    index < rating ? "fill-yellow-400 text-yellow-400" : "text-gray-400"
                }`} 
            />
        ));
    };

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            setLoading(true);
            await Promise.all([fectchMovieData(), fetchComments()]);
            setLoading(false);
        };
        loadData();
    }, [id]);
    
    if(error) return (
        <div className="text-center mt-4 py-2">
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
            </div>
        </div>
    );

    if (loading) return (
        <div className="text-center mt-4 py-2">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
            <p className="mt-2">Loading movie...</p>
        </div>
    );
    const movie = movieData;
    return (
        <div className="p-4 bg-dark-900 text-white">
            <div className="max-w-4xl mx-auto mx-auto flex flex-col md:flex-row">
                <img src={movie?.poster} alt={movie?.title} className="w-full md:w-auto  h-auto rounded-lg mb-4 md:mb-0 md:mr-6" />
                <div>
                    <h1 className="text-4xl font-bold">{movie?.title}</h1>
                    <p className="text-gray-400">{movie?.runtime ?? "N/A"} • {movie?.year ?? "N/A"} • {movie?.rating ?? "N/A"}/10⭐ </p>
                    <p className="text-lg mt-4 max-h-40 overflow-auto no-scrollbar">{movie?.summary}</p>

                    <h3 className="mt-6 text-xl font-semibold">Director</h3>
                    <p>{movie?.director?.length? movie.director.join(", ") : "No director available"}</p>

                    <h3 className="mt-6 text-xl font-semibold">Cast</h3>
                    <p>{movie?.cast?.length? movie.cast.join(", ") : "No cast available"}</p>
                    <h3 className="text-2xl mt-8">Genres</h3>
                    <ul className="grid grid-cols-3 gap-4">
                        {movie?.genres.map((genre) => (
                            <li key={genre} className="bg-gray-800 px-2 py-1 rounded-lg text-center">{genre}</li>
                        ))}
                    </ul>
                    <div className="flex space-x-4 mt-8">
                        <span className="bg-gray-800 px-4 py-2 rounded-lg text-center">720p</span>
                        <span className="bg-gray-800 px-4 py-2 rounded-lg text-center">1080p</span>
                    </div>
                </div>
            </div>
        </div>
    );
}