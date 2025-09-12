"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Star, MessageCircle, Send, X } from "lucide-react";
import { Movie, Torrent } from "../types/movies";
import { Comment } from "../types/comment";
import { useAuth } from "../../context/authcontext";
import { parsedError } from "../../ui/error/parsedError";
import { formatDate, renderStars } from "../../ui/comments";
import { useTranslation } from "react-i18next";

export default function MovieDetails() {
    const { user, logout, isLoading: authLoading } = useAuth();
    const { id } = useParams();
    const [movieData, setMovieData] = useState<Movie | null>(null);
    const [error, setError] = useState<string[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [comments, setComments] = useState<Comment[]>([]);
    const [commentError, setCommentError] = useState<string[] | null>(null);
    const [commentsLoading, setCommentsLoading] = useState(false);
    const [newComment, setNewComment] = useState("");
    const [newRating, setNewRating] = useState(5);
    const [submitting, setSubmitting] = useState(false);
    const [hascommented, setHasCommented] = useState(false);
    const [userComment, setUserComment] = useState<Comment | null>(null);
    const [isStreamingModalOpen, setisStreamModalOpen] = useState(false);
    const [selectedTorrent, setSelectedTorrent] = useState<Torrent | null>(null);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const { t } = useTranslation();

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
                setError(text);
                return;
            }
            const data = await response.json();
            setMovieData(data);
            console.log("Movie data:", data);
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
                setError(text);
                return;
            }
            const data = await response.json();
            setComments(data);
            if(user){
                const ownComment = data.find((comment: Comment) => comment.username === user.username);
                if (ownComment) {
                    setHasCommented(true);
                    setUserComment(ownComment)
                }
            }
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
        setCommentError(null);
        const token = localStorage.getItem("token");
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    comment: newComment.trim(),
                    movie_id: id as string,
                    rating: newRating,
                }),
            });
            if (!response.ok) {
                if (response.status === 401) logout();
                const text = parsedError(await response.json());
                setCommentError(text);
                return;
            }
            setNewComment("");
            setNewRating(5);
            await fetchComments();
        } catch (err) {
            setCommentError(err as string[]);
        } finally {
            setSubmitting(false);
        }
    };

    const  handleTorrentSelect = async (torrent: Torrent) => {
        if (!id) return;
        setSelectedTorrent(torrent);
        setisStreamModalOpen(true);
        setTimeout(() => {
            if (videoRef.current) {
                videoRef.current.src = URL.createObjectURL(mediaSource);
                console.log("Iniciando streaming para torrent:", torrent);
            } else {
                console.error("videoRef no está asignado");
            }
        }, 0);
        const mediaSource = new MediaSource();
        const token = localStorage.getItem("token");
        mediaSource.addEventListener("sourceopen", async () => {
            console.log("MediaSource abierto correctamente");
            try {
                const mimeCodec = 'video/mp4; codecs="avc1.42E01E, mp4a.40.2"';
                if (!MediaSource.isTypeSupported(mimeCodec)) {
                    console.error("El codec no es compatible:", mimeCodec);
                    return;
                }
                const sourceBuffer = mediaSource.addSourceBuffer(mimeCodec);
                console.log("SourceBuffer creado con codec:", mimeCodec);
        
                const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/movies/${id}/stream?torrent_hash=${torrent.hash}`, {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                console.log("Respuesta del servidor:", response);
        
                if (!response.ok) {
                    if (response.status === 401) logout();
                    const text = parsedError(await response.json());
                    setCommentError(text);
                    return;
                }
        
                const reader = response.body?.getReader();
                if (!reader) {
                    setCommentError(["No response body"]);
                    return;
                }
                console.log("Comenzando a leer el stream...");
        
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        console.log("Lectura del stream completada");
                        if (sourceBuffer.updating) {
                            console.log("Esperando a que el SourceBuffer termine de actualizarse...");
                            await new Promise((resolve) => {
                                sourceBuffer.addEventListener("updateend", resolve, { once: true });
                            });
                        }
                        if (mediaSource.readyState === "open") {
                            mediaSource.endOfStream();
                            console.log("MediaSource cerrado correctamente.");
                        }
                        break;
                    }
                    if (value) {
                        console.log("Datos leídos (tamaño):", value.byteLength);
                        await new Promise((resolve, reject) => {
                            try {
                                if (!sourceBuffer.updating) {
                                    sourceBuffer.appendBuffer(value);
                                } else {
                                    console.warn("El SourceBuffer está actualizando, esperando...");
                                    sourceBuffer.addEventListener("updateend", () => {
                                        sourceBuffer.appendBuffer(value);
                                        resolve("Datos agregados correctamente");
                                    }, { once: true });
                                }
                                sourceBuffer.addEventListener("error", (err) => {
                                    console.error("Error al actualizar el SourceBuffer:", err);
                                    reject(err);
                                }, { once: true });
                            } catch (err) {
                                console.error("Error al intentar agregar datos al SourceBuffer:", err);
                                reject(err);
                            }
                        });
                    }
                }
            } catch (err) {
                console.error("Error en el manejo del torrent:", err);
                setCommentError(err as string[]);
                if (mediaSource.readyState === "open") {
                    mediaSource.endOfStream();
                }
            }
        });
    };

    const closeStreamingModal = () => {
        setisStreamModalOpen(false);
        setSelectedTorrent(null);
        if (videoRef.current) {
            videoRef.current.pause();
            videoRef.current.src = "";
            videoRef.current.load();
        }
    };

    useEffect(() => {
        if (authLoading) return;
        const loadData = async () => {
            setLoading(true);
            await Promise.all([fectchMovieData(), fetchComments()]);
            setLoading(false);
        };
        loadData();
    }, [id, authLoading]);

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
            <p className="mt-2">{t("movies.loading")}</p>
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
                    <p>{movie?.director?.length? movie.director.join(", ") : t("movies.noDirector")}</p>

                    <h3 className="mt-6 text-xl font-semibold">{t("movies.cast")}</h3>
                    <p>{movie?.cast?.length? movie.cast.join(", ") : t("movies.noCast")}</p>
                    <h3 className="text-2xl mt-8">{t("movies.genres")}</h3>
                    <ul className="grid grid-cols-3 gap-4">
                        {movie?.genres.map((genre) => (
                            <li key={genre} className="bg-gray-800 px-2 py-1 rounded-lg text-center">{genre}</li>
                        ))}
                    </ul>
                    {typeof movie?.view_percentage === "number" && (
                        <div className="mt-6">
                            <p className="text-sm text-gray-400 mb-1">{t("movies.viewing")}</p>
                            <div className="w-full h-4 bg-gray-800 rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all duration-500 ease-in-out ${
                                movie.view_percentage === 100
                                    ? "bg-green-500"
                                    : movie.view_percentage >= 75
                                    ? "bg-blue-500"
                                    : movie.view_percentage >= 50
                                    ? "bg-yellow-500"
                                    : "bg-red-500"
                                }`}
                                style={{ width: `${movie.view_percentage}%` }}
                            />
                            </div>
                            <p className="text-xs text-gray-400 mt-1">
                            {movie.view_percentage === 100
                                ? t("movies.completed")
                                : `${movie.view_percentage}%`}
                            </p>
                        </div>
                    )}
                    {movie?.torrents && movie.torrents.length > 0 && (
                    <div className="mt-8">
                        <div className="flex flex-wrap gap-3">
                            {movie.torrents.map((torrent, index) => (
                                <button
                                    key={index}
                                    className="bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg text-center transition-colors cursor-pointer border border-gray-600 hover:border-gray-500"
                                    onClick={() => {
                                        handleTorrentSelect(torrent);
                                    }}
                                >
                                    <div className="flex flex-col items-center">
                                        <span className="font-medium">{torrent.quality}</span>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                    )}
                </div>
            </div>

            {hascommented && userComment ? (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold mb-4">{t("movies.comment")}</h2>
                    <div className="bg-gray-700 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                                    {userComment.username.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <p className="font-medium">{userComment.username}</p>
                                    <p className="text-xs text-gray-400">
                                        {formatDate(userComment.created_at)}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-1">
                                {renderStars(userComment.rating)}
                                <span className="ml-1 text-sm text-gray-400">
                                    ({userComment.rating}/5)
                                </span>
                            </div>
                        </div>
                        <p className="text-gray-200 leading-relaxed">{userComment.comment}</p>
                    </div>
                </div>
            ) : (
                <form onSubmit={submitComment} className="mb-8">
                    {commentError && Array.isArray(commentError) && (
                        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                            {commentError.map((err, index) => (
                                <div key={index}>{err}</div>
                            ))}
                        </div>
                    )}               
                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2">{t("movies.rating")}</label>
                        <div className="flex gap-1">
                            {Array.from({ length: 5 }, (_, i) => (
                                <button
                                    key={i}
                                    type="button"
                                    onClick={() => setNewRating(i + 1)}
                                    className="focus:outline-none"
                                >
                                    <Star
                                        className={`w-6 h-6 transition-colors ${
                                            i < newRating 
                                                ? "fill-yellow-400 text-yellow-400 hover:fill-yellow-300" 
                                                : "text-gray-400 hover:text-yellow-300"
                                        }`}
                                    />
                                </button>
                            ))}
                            <span className="ml-2 text-sm text-gray-400">({newRating}/5)</span>
                        </div>
                    </div>

                    <div className="mb-4">
                        <label htmlFor="comment" className="block text-sm font-medium mb-2">
                            {t("movies.comment")}
                        </label>
                        <textarea
                            id="comment"
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 resize-none"
                            rows={4}
                            placeholder={t("movies.placeholder")}
                            disabled={submitting}
                            maxLength={1000}
                        />
                        <div className="text-xs text-gray-400 mt-1">
                            {newComment.length}/1000 {t("movies.character")}
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={!newComment.trim() || newComment.length > 1000 || submitting}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-2 rounded-lg transition-colors"
                    >
                        <Send className="w-4 h-4" />
                        {submitting ? t("movies.sending") : t("movies.submitComment")}
                    </button>
                </form>
            )}
            <div className="space-y-4">
                {commentsLoading ? (
                    <div className="text-center py-8">
                        <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-white"></div>
                        <p className="mt-2">{t("movies.loading")}</p>
                    </div>
                ) : comments.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                        <MessageCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                        <p>{t("movies.firstComment")}</p>
                    </div>
                ) : (
                    comments.map((comment) => (
                        <div key={comment.id} className="bg-gray-700 rounded-lg p-4">
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                                        {comment.username.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                        <Link href={`/profile/${comment.username}`}>
                                            <p className="font-medium hover:text-blue-400 cursor-pointer">
                                                {comment.username}
                                            </p>
                                        </Link>
                                        <p className="text-xs text-gray-400">
                                            {formatDate(comment.created_at)}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1">
                                    {renderStars(comment.rating)}
                                    <span className="ml-1 text-sm text-gray-400">
                                        ({comment.rating}/5)
                                    </span>
                                </div>
                            </div>
                            <p className="text-gray-200 leading-relaxed">{comment.comment}</p>
                        </div>
                    ))
                )}
            </div>
            {isStreamingModalOpen && (
                <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50">
                <div className="bg-gray-800 rounded-lg w-full h-full m-4 relative">
                    <div className="flex items-center justify-between p-4 border-b border-gray-700">
                    <h2 className="text-lg font-semibold">
                        {movie?.title} - {selectedTorrent?.quality}
                    </h2>
                    <button onClick={closeStreamingModal} className="p-1 rounded-full hover:bg-gray-700 transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                    </div>
                    <div className="flex-1 flex items-center justify-center p-4">
                    <video ref={videoRef} controls autoPlay className="w-full h-full object-contain bg-black" />
                    </div>
                </div>
                </div>
            )}
        </div>
    );
}