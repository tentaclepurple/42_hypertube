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
    const [availableSubtitles, setAvailableSubtitles] = useState<any[]>([]);
    const [loadingSubtitles, setLoadingSubtitles] = useState(false);
    const [subtitleError, setSubtitleError] = useState<string | null>(null);
    const lastUpdateTimeRef = useRef(Date.now());
    const lastUpdatePercentageRef = useRef(0);
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

    const loadSubtitles = async (torrent: Torrent) => {
        if (!id) return [];
        
        setLoadingSubtitles(true);
        setSubtitleError(null);
        const token = localStorage.getItem("token");
        
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_URL}/api/v1/movies/${id}/subtitles?torrent_hash=${torrent.hash}`,
                {
                    method: "GET",
                    headers: { Authorization: `Bearer ${token}` },
                }
            );
            
            if (!response.ok) {
                if (response.status === 401) logout();
                console.warn('No subtitles available or error loading them');
                return [];
            }
            
            const data = await response.json();
            const subtitles = data.subtitles || [];
            setAvailableSubtitles(subtitles);
            console.log("Subtitles loaded:", subtitles);
            return subtitles;
            
        } catch (error) {
            console.error('Error loading subtitles:', error);
            setSubtitleError('Failed to load subtitles');
            return [];
        } finally {
            setLoadingSubtitles(false);
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

    const updateViewProgress = async (percentage: number) => {
        if (!id) return;
        const token = localStorage.getItem("token");
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/movies/${id}/view`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ view_percentage: Math.floor(percentage) }),
            });
            if (!response.ok) {
                if (response.status === 401) logout();
                const text = parsedError(await response.json());
                setError(text);
                return;
            }
        } catch (err) {
            setError(err as string[]);
        }
    }

    // Función para convertir SRT a WebVTT
    const srtToVtt = (srtContent: string): string => {
        let vttContent = 'WEBVTT\n\n';
        vttContent += srtContent.replace(/(\d{2}:\d{2}:\d{2}),(\d{3})/g, '$1.$2');
        return vttContent;
    };

    // Función mejorada para detectar idioma del nombre del archivo
    const detectLanguageFromFilename = (filename: string): string => {
        const lowerFilename = filename.toLowerCase();
        
        const patterns = [
            { pattern: /spanish|español|esp|spa|es\b|castellano|cast/i, language: 'Spanish' },
            { pattern: /english|eng|en\b|ingles/i, language: 'English' },
            { pattern: /french|français|fr\b|fra|francais/i, language: 'French' },
            { pattern: /german|deutsch|de\b|ger|aleman/i, language: 'German' },
            { pattern: /italian|italiano|it\b|ita/i, language: 'Italian' },
            { pattern: /portuguese|português|pt\b|por|portugues/i, language: 'Portuguese' },
        ];
        
        for (const { pattern, language } of patterns) {
            if (pattern.test(lowerFilename)) {
                return language;
            }
        }
        
        return filename || 'Unknown';
    };

    // Función auxiliar para mapear códigos de idioma
    const mapLanguageCode = (language: string): string => {
        const langMap: { [key: string]: string } = {
            'spanish': 'es',
            'español': 'es',
            'english': 'en',
            'inglés': 'en',
            'french': 'fr',
            'français': 'fr',
            'francés': 'fr',
            'german': 'de',
            'deutsch': 'de',
            'alemán': 'de',
            'italian': 'it',
            'italiano': 'it',
            'portuguese': 'pt',
            'português': 'pt',
            'portugués': 'pt'
        };
        
        const lowerLang = language.toLowerCase();
        for (const [key, value] of Object.entries(langMap)) {
            if (lowerLang.includes(key)) {
                return value;
            }
        }
        
        const match = language.match(/^([a-z]{2})\b/i);
        return match ? match[1].toLowerCase() : 'en';
    };

    // Función corregida para manejar subtítulos con conversión a WebVTT
    const handleLoadedMetadata = async (subtitles: any[], currentTorrent: Torrent) => {
        console.log('Video metadata loaded, processing subtitles...');
        console.log('Available subtitles:', subtitles);
        
        // Procesar cada subtítulo de forma asíncrona
        for (let index = 0; index < subtitles.length; index++) {
            const subtitle = subtitles[index];
            console.log(`Processing subtitle ${index}:`, subtitle);
            
            try {
                // Cargar el contenido SRT
                const subtitleUrl = `/api/subtitles/${id}/${subtitle.relative_path}?torrent_hash=${currentTorrent.hash}`;
                console.log(`Loading subtitle from: ${subtitleUrl}`);
                
                const response = await fetch(subtitleUrl);
                if (!response.ok) {
                    console.error(`Failed to load subtitle ${index}: ${response.status}`);
                    continue;
                }
                
                const srtContent = await response.text();
                console.log(`Subtitle ${index} content length:`, srtContent.length);
                
                // Convertir SRT a WebVTT
                const vttContent = srtToVtt(srtContent);
                
                // Crear blob WebVTT
                const blob = new Blob([vttContent], { type: 'text/vtt; charset=utf-8' });
                const blobUrl = URL.createObjectURL(blob);
                
                // Crear elemento track
                const track = document.createElement('track');
                track.kind = 'subtitles';
                track.src = blobUrl;
                
                // Configurar idioma y etiquetas
                const detectedLanguage = detectLanguageFromFilename(subtitle.filename || subtitle.language || 'Unknown');
                const langCode = mapLanguageCode(detectedLanguage);
                
                track.srclang = langCode;
                track.label = detectedLanguage;
                
                // Configurar subtítulo por defecto (español si está disponible, sino el primero)
                const isSpanish = detectedLanguage.toLowerCase().includes('spanish') || 
                                detectedLanguage.toLowerCase().includes('español') ||
                                langCode === 'es';
                
                track.default = false;
                
                console.log('Adding WebVTT subtitle track:', {
                    index,
                    srclang: track.srclang,
                    label: track.label,
                    default: track.default,
                    blobUrl: blobUrl.substring(0, 50) + '...'
                });
                
                // Añadir track al video
                videoRef.current?.appendChild(track);
                
                // Verificar y activar el track después de un momento
                setTimeout(() => {
                    const textTrack = videoRef.current?.textTracks[videoRef.current.textTracks.length - 1];
                    if (textTrack) {
                        console.log(`Track ${index} added successfully:`, {
                            kind: textTrack.kind,
                            label: textTrack.label,
                            language: textTrack.language,
                            mode: textTrack.mode,
                            cues: textTrack.cues ? textTrack.cues.length : 'not loaded'
                        });
                        
                        // Activar si es el predeterminado
                        if (track.default) {
                            textTrack.mode = 'showing';
                            console.log(`Activated default track ${index}`);
                        }
                    }
                }, 100 * (index + 1)); // Escalonar la verificación
                
            } catch (error) {
                console.error(`Error processing subtitle ${index}:`, error);
            }
        }
        
        // Verificación final después de procesar todos los subtítulos
        setTimeout(() => {
            if (videoRef.current && videoRef.current.textTracks) {
                console.log('Final subtitle tracks check:', videoRef.current.textTracks.length);
                
                for (let i = 0; i < videoRef.current.textTracks.length; i++) {
                    const track = videoRef.current.textTracks[i];
                    console.log(`Final Track ${i}:`, {
                        kind: track.kind,
                        label: track.label,
                        language: track.language,
                        mode: track.mode,
                        cues: track.cues ? track.cues.length : 'not loaded'
                    });
                }
                
                // Si no hay ningún track activo, activar el primero
                let hasActiveTrack = false;
                for (let i = 0; i < videoRef.current.textTracks.length; i++) {
                    if (videoRef.current.textTracks[i].mode === 'showing') {
                        hasActiveTrack = true;
                        break;
                    }
                }
                
                if (!hasActiveTrack && videoRef.current.textTracks.length > 0) {
                    videoRef.current.textTracks[0].mode = 'showing';
                    console.log('Activated first track as fallback');
                }
            }
        }, 2000);
    };

    const handleTorrentSelect = async (torrent: Torrent) => {
        if (!id) return;
        
        setSelectedTorrent(torrent);
        setisStreamModalOpen(true);
        setCommentError(null);
        lastUpdatePercentageRef.current = movieData?.view_percentage || 0;
        lastUpdateTimeRef.current = Date.now();
        
        setTimeout(async () => {
            if (videoRef.current) {
                const streamUrl = `${process.env.NEXT_PUBLIC_URL}/api/v1/movies/${id}/stream?torrent_hash=${torrent.hash}`;

                try {
                    const checkResponse = await fetch(streamUrl, {
                        method: "GET",
                        credentials: 'include',
                    });

                    if (checkResponse.status === 202) {
                        const statusResponse = await fetch(streamUrl, {
                            method: "GET",
                            credentials: 'include',
                        });
                        const data = await statusResponse.json();
                        
                        const message = data.detail?.message || 'Download in progress';
                        const retryAfter = data.detail?.retry_after || 30;
                        
                        setCommentError([`${message} - Retrying in ${retryAfter}s...`]);
                        
                        setTimeout(() => handleTorrentSelect(torrent), retryAfter * 1000);
                        return;
                    }
                    
                    if (!checkResponse.ok) {
                        if (checkResponse.status === 401) logout();
                        setCommentError([`Stream error: ${checkResponse.status}`]);
                        return;
                    }
                    
                    videoRef.current.src = streamUrl;
                    
                    // Cargar subtítulos disponibles
                    const subtitles = await loadSubtitles(torrent);
                    console.log('Subtitles loaded for processing:', subtitles);

                    // Limpiar tracks de subtítulos existentes ANTES de cargar
                    const existingTracks = videoRef.current.querySelectorAll('track');
                    existingTracks.forEach(track => {
                        console.log('Removing existing track:', track.src);
                        track.remove();
                    });

                    const handleError = (e: Event) => {
                        const video = e.target as HTMLVideoElement;
                        if (video.error) {
                            console.error('Video error:', video.error);
                            setCommentError([`Video error: ${video.error.message || 'Playback failed'}`]);
                        }
                    };
                    
                    const handleLoadedData = () => {
                        setCommentError(null);
                        console.log('Video data loaded');
                    };
                    
                    const handleProgress = () => {
                        if (videoRef.current && videoRef.current.buffered.length > 0) {
                            const buffered = videoRef.current.buffered.end(0);
                            const duration = videoRef.current.duration || 0;
                            if (duration > 0) {
                                const percent = (buffered / duration) * 100;
                                console.log(`Buffered: ${percent.toFixed(2)}%`);
                            }
                        }
                    };

                    const handleTimeUpdate = () => {
                        if (videoRef.current && videoRef.current.duration > 0) {
                            const currentTime = videoRef.current.currentTime;
                            const duration = videoRef.current.duration;
                            const percentage = (currentTime / duration) * 100;
                            const now = Date.now();
                            const timeDiff = now - lastUpdateTimeRef.current;
                            const currentPercentage = Math.floor(percentage);
                            const lastReported = lastUpdatePercentageRef.current;

                            if (timeDiff >= 30000 && currentPercentage > lastReported) {
                                updateViewProgress(percentage);
                                lastUpdateTimeRef.current = now;
                                lastUpdatePercentageRef.current = currentPercentage;
                                if (movieData) {
                                    setMovieData({
                                        ...movieData,
                                        view_percentage: currentPercentage
                                    });
                                }
                            }
                        }
                    };

                    // Limpiar eventos anteriores
                    videoRef.current.removeEventListener('error', handleError);
                    videoRef.current.removeEventListener('loadeddata', handleLoadedData);
                    videoRef.current.removeEventListener('loadedmetadata', () => {});
                    videoRef.current.removeEventListener('progress', handleProgress);
                    videoRef.current.removeEventListener('timeupdate', handleTimeUpdate);
                    
                    // Añadir eventos - NOTA: Pasamos los parámetros correctos a handleLoadedMetadata
                    videoRef.current.addEventListener('error', handleError);
                    videoRef.current.addEventListener('loadeddata', handleLoadedData);
                    videoRef.current.addEventListener('loadedmetadata', () => handleLoadedMetadata(subtitles, torrent));
                    videoRef.current.addEventListener('progress', handleProgress);
                    videoRef.current.addEventListener('timeupdate', handleTimeUpdate);
                    
                    // Iniciar carga
                    videoRef.current.load();
                    
                    // Debugging adicional
                    setTimeout(() => {
                        if (videoRef.current) {
                            console.log('Video tracks after load:', videoRef.current.textTracks.length);
                            for (let i = 0; i < videoRef.current.textTracks.length; i++) {
                                const track = videoRef.current.textTracks[i];
                                console.log(`Track ${i}:`, {
                                    kind: track.kind,
                                    label: track.label,
                                    language: track.language,
                                    mode: track.mode,
                                    cues: track.cues ? track.cues.length : 'not loaded'
                                });
                            }
                        }
                    }, 5000);
                    
                } catch (error) {
                    console.error('Network error:', error);
                    setCommentError([`Network error: ${error}`]);
                }
            } else {
                setError(["VideoRef still null after timeout"]);
            }
        }, 100);
    };

    const closeStreamingModal = () => {
        setisStreamModalOpen(false);
        setSelectedTorrent(null);
        setAvailableSubtitles([]);
        setSubtitleError(null);
        lastUpdateTimeRef.current = Date.now();
        
        if (videoRef.current) {
            videoRef.current.pause();
            videoRef.current.removeEventListener('error', () => {});
            videoRef.current.removeEventListener('loadeddata', () => {});
            videoRef.current.removeEventListener('loadedmetadata', () => {});
            videoRef.current.removeEventListener('progress', () => {});
            videoRef.current.removeEventListener('timeupdate', () => {});
            
            // Limpiar tracks de subtítulos y revocar blob URLs
            const tracks = videoRef.current.querySelectorAll('track');
            tracks.forEach(track => {
                if (track.src.startsWith('blob:')) {
                    URL.revokeObjectURL(track.src);
                }
                track.remove();
            });
            
            videoRef.current.currentTime = 0;
            videoRef.current.removeAttribute('src');
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
                                movie.view_percentage >= 90
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
                            {movie.view_percentage >= 90
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
                                    onClick={() => handleTorrentSelect(torrent)}
                                >
                                    <div className="flex flex-col items-center">
                                        <span className="font-medium">{torrent.quality}</span>
                                        {loadingSubtitles && selectedTorrent?.hash === torrent.hash && (
                                            <span className="text-xs text-blue-400">Loading subtitles...</span>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                        {subtitleError && (
                            <div className="mt-2 text-sm text-yellow-400">
                                {subtitleError}
                            </div>
                        )}
                        {availableSubtitles.length > 0 && (
                            <div className="mt-4 p-3 bg-gray-800 rounded-lg">
                                <p className="text-sm text-gray-300 mb-2">Available subtitles ({availableSubtitles.length}):</p>
                                <div className="flex flex-wrap gap-2">
                                    {availableSubtitles.map((subtitle) => (
                                        <span
                                            key={subtitle.id}
                                            className="text-xs bg-blue-600 px-2 py-1 rounded"
                                            title={subtitle.filename}
                                        >
                                            {subtitle.language}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
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
