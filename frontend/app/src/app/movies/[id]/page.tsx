"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Star, MessageCircle, Send, X, Heart, Pencil, Trash2, Check } from "lucide-react";
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
    const [subtitleError, setSubtitleError] = useState<string | null>(null);
    const [isButtonDisabled, setIsButtonDisabled] = useState(false);
    const [isFavorite, setIsFavorite] = useState(false);
    const [isPreparingStream, setIsPreparingStream] = useState(false);
    const [editingUserComment, setEditingUserComment] = useState(false);
    const [editUserCommentText, setEditUserCommentText] = useState({
        comment: "",
        rating: 1,
    });
    const [editUserCommentError, setEditUserCommentError] = useState<string[] | null>(null);
    
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

    const fecthFavoriteStatus = async () => {
        if (!id) return;
        const token = localStorage.getItem("token");
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/user-activity/check-favorite/${id}`, {
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
            setIsFavorite(data.is_favorite);
        } catch (err) {
            setError(err as string[]);
        }
    };

    const toggleFavorite = async () => {
        if (!id || isButtonDisabled) return;

        setIsButtonDisabled(true);
        const token = localStorage.getItem("token");
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/user-activity/favorites/${id}/toggle`, {
                method: "POST",
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
            setIsFavorite(data.is_favorite);
        } catch (err) {
            setError(err as string[]);
        } finally {
            setTimeout(() => {
                setIsButtonDisabled(false);
            }, 5000);
        }
    };

    const handleEditUserComment = () => {
        if (userComment) {
            setEditingUserComment(true);
            setEditUserCommentText({
                comment: userComment.comment,
                rating: userComment.rating,
            });
            setEditUserCommentError(null);
        }
    };

    const handleCancelEditUserComment = () => {
        setEditingUserComment(false);
        setEditUserCommentText({ comment: "", rating: 1 });
        setEditUserCommentError(null);
    };

    const handleSaveEditUserComment = async () => {
        if (!editUserCommentText.comment.trim()) {
            setEditUserCommentError(['Comment cannot be empty']);
            return;
        }

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                logout();
                return;
            }

            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/${userComment?.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(editUserCommentText),
            });

            if (!response.ok) {
                if (response.status === 401) {
                    logout();
                    return;
                }
                const errorData = await response.json();
                const errorText = parsedError(errorData);
                throw errorText;
            }

            const updatedComment = await response.json();
            setUserComment(updatedComment);
            setEditUserCommentError(null);
            setEditingUserComment(false);
            setEditUserCommentText({ comment: "", rating: 1 });
        } catch (err) {
            console.error('Error updating comment:', err);
            setEditUserCommentError(['Failed to update comment. Please try again.']);
        }
    };

    const handleUserCommentInputChange = (field: string, value: any) => {
        setEditUserCommentText(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleDeleteUserComment = async () => {
        if (!window.confirm(t("profile.delete") || "Are you sure you want to delete this comment?")) {
            return;
        }

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                logout();
                return;
            }

            const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/v1/comments/${userComment?.id}`, {
                method: 'DELETE',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    logout();
                    return;
                }
                const errorData = await response.json();
                const errorText = parsedError(errorData);
                throw errorText;
            }

            setUserComment(null);
            setHasCommented(false);
            setEditingUserComment(false);
            setEditUserCommentText({ comment: "", rating: 1 });
            setEditUserCommentError(null);
        } catch (err) {
            console.error('Error deleting comment:', err);
            setError(['Failed to delete comment. Please try again.']);
        }
    };
    
    const loadSubtitles = async (torrent: Torrent) => {
        if (!id) return [];
        
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
            console.log("Subtitles loaded:", subtitles);
            return subtitles;
            
        } catch (error) {
            console.error('Error loading subtitles:', error);
            setSubtitleError('Failed to load subtitles');
            return [];
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


    const srtToVtt = (srtContent: string): string => {
        let vttContent = 'WEBVTT\n\n';
        vttContent += srtContent.replace(/(\d{2}:\d{2}:\d{2}),(\d{3})/g, '$1.$2');
        return vttContent;
    };

    const detectLanguageFromFilename = (filename: string): string => {
        const lowerFilename = filename.toLowerCase();
        
        const patterns = [
            { pattern: /spanish|español|castellano|cast/i, language: 'Spanish' },
            { pattern: /english|eng|ingles/i, language: 'English' },
            { pattern: /french|français|francais/i, language: 'French' },
            { pattern: /german|deutsch|ger|aleman/i, language: 'German' },
            { pattern: /italian|italiano/i, language: 'Italian' },
            { pattern: /portuguese|português|portugues/i, language: 'Portuguese' },
        ];
        
        for (const { pattern, language } of patterns) {
            if (pattern.test(lowerFilename)) {
                return language;
            }
        }
        
        return filename || 'Unknown';
    };

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

    const handleLoadedMetadata = async (subtitles: any[], currentTorrent: Torrent) => {
        console.log('Video metadata loaded, processing subtitles...');
        console.log('Available subtitles:', subtitles);

        for (let index = 0; index < subtitles.length; index++) {
            const subtitle = subtitles[index];
            console.log(`Processing subtitle ${index}:`, subtitle);
            
            try {

                const subtitleUrl = `/api/subtitles/${id}/${subtitle.relative_path}?torrent_hash=${currentTorrent.hash}`;
                console.log(`Loading subtitle from: ${subtitleUrl}`);
                
                const response = await fetch(subtitleUrl);
                if (!response.ok) {
                    console.error(`Failed to load subtitle ${index}: ${response.status}`);
                    continue;
                }
                
                const srtContent = await response.text();
                console.log(`Subtitle ${index} content length:`, srtContent.length);

                const vttContent = srtToVtt(srtContent);

                const blob = new Blob([vttContent], { type: 'text/vtt; charset=utf-8' });
                const blobUrl = URL.createObjectURL(blob);

                const track = document.createElement('track');
                track.kind = 'subtitles';
                track.src = blobUrl;

                const detectedLanguage = detectLanguageFromFilename(subtitle.filename || subtitle.language || 'Unknown');
                const langCode = mapLanguageCode(detectedLanguage);
                
                track.srclang = langCode;
                track.label = detectedLanguage;

                track.default = false;
                
                console.log('Adding WebVTT subtitle track:', {
                    index,
                    srclang: track.srclang,
                    label: track.label,
                    default: track.default,
                    blobUrl: blobUrl.substring(0, 50) + '...'
                });

                videoRef.current?.appendChild(track);

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

                        if (track.default) {
                            textTrack.mode = 'showing';
                            console.log(`Activated default track ${index}`);
                        }
                    }
                }, 100 * (index + 1));
                
            } catch (error) {
                console.error(`Error processing subtitle ${index}:`, error);
            }
        }

        setTimeout(() => {
            if (videoRef.current && videoRef.current.textTracks) {
                console.log('Final subtitle tracks check:', videoRef.current.textTracks.length);
                
                for (let i = 0; i < videoRef.current.textTracks.length; i++) {
                    const track = videoRef.current.textTracks[i];
                    track.mode = 'disabled';
                    console.log(`Track ${i} disabled:`, {
                        kind: track.kind,
                        label: track.label,
                        language: track.language,
                        mode: track.mode,
                        cues: track.cues ? track.cues.length : 'not loaded'
                    });
                }
                console.log('Subtitle tracks available but remaining disabled by user choice');
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
                const token = localStorage.getItem("token");
                const streamUrl = `${process.env.NEXT_PUBLIC_URL}/api/v1/movies/${id}/stream?torrent_hash=${torrent.hash}&token=${encodeURIComponent(token || "")}`;
                try {
                    const checkResponse = await fetch(streamUrl, {
                        method: "GET",
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    if (checkResponse.status === 202) {
                        const statusUrl = `${process.env.NEXT_PUBLIC_URL}/api/v1/movies/${id}/stream/status?torrent_hash=${torrent.hash}`;
                        const statusResponse = await fetch(statusUrl, {
                            method: "GET",
                            headers: {
                                Authorization: `Bearer ${token}`
                            }
                        });
                        setIsPreparingStream(true);
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
                        setIsPreparingStream(false)
                        return;
                    }

                    console.log('Setting video source:', streamUrl.substring(0, 100) + '...');
                    videoRef.current.src = streamUrl;
                    const subtitles = await loadSubtitles(torrent);
                    console.log('Subtitles loaded for processing:', subtitles);
                    const existingTracks = videoRef.current.querySelectorAll('track');
                    existingTracks.forEach(track => {
                        console.log('Removing existing track:', track.src);
                        track.remove();
                    });
                    const handleError = (e: Event) => {
                        const video = e.target as HTMLVideoElement;
                        if (video.error) {
                            console.error('Video error:', video.error);
                            let errorMessage = 'Playback failed';
                            switch (video.error.code) {
                                case 1: // MEDIA_ERR_ABORTED
                                    errorMessage = 'Video loading aborted';
                                    break;
                                case 2: // MEDIA_ERR_NETWORK
                                    errorMessage = 'Network error while loading video';
                                    break;
                                case 3: // MEDIA_ERR_DECODE
                                    errorMessage = 'Video decoding failed';
                                    break;
                                case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
                                    errorMessage = 'Video format not supported';
                                    break;
                            }
                            setCommentError([`Video error: ${errorMessage}`]);
                        }
                    };
                    const handleLoadedData = () => {
                        setCommentError(null);
                        setIsPreparingStream(false);
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
                    
                    videoRef.current.removeEventListener('error', handleError);
                    videoRef.current.removeEventListener('loadeddata', handleLoadedData);
                    videoRef.current.removeEventListener('loadedmetadata', () => {});
                    videoRef.current.removeEventListener('progress', handleProgress);
                    videoRef.current.removeEventListener('timeupdate', handleTimeUpdate);
                    
                    videoRef.current.addEventListener('error', handleError);
                    videoRef.current.addEventListener('loadeddata', handleLoadedData);
                    videoRef.current.addEventListener('loadedmetadata', () => handleLoadedMetadata(subtitles, torrent));
                    videoRef.current.addEventListener('progress', handleProgress);
                    videoRef.current.addEventListener('timeupdate', handleTimeUpdate);
                    videoRef.current.load();
                    
                    setTimeout(() => {
                        if (videoRef.current) {
                            setIsPreparingStream(false);
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
                    setIsPreparingStream(false);
                    setCommentError([`Network error: ${error}`]);
                }
            } else {
                setError(["Video element not ready"]);
            }
        }, 100);
    };

    const closeStreamingModal = () => {
        setisStreamModalOpen(false);
        setSelectedTorrent(null);
        setSubtitleError(null);
        lastUpdateTimeRef.current = Date.now();
        
        if (videoRef.current) {
            videoRef.current.pause();
            videoRef.current.removeEventListener('error', () => {});
            videoRef.current.removeEventListener('loadeddata', () => {});
            videoRef.current.removeEventListener('loadedmetadata', () => {});
            videoRef.current.removeEventListener('progress', () => {});
            videoRef.current.removeEventListener('timeupdate', () => {});

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
            await Promise.all([fectchMovieData(), fetchComments(), fecthFavoriteStatus()]);
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
            <div className="max-w-4xl mx-auto flex flex-col md:flex-row">
                <div className="flex-shrink-0">
                    <img src={movie?.poster} alt={movie?.title} className="w-full md:w-auto  h-auto rounded-lg mb-4 md:mb-0 md:mr-6" />
                </div>
                <div>
                    <h1 className="text-4xl font-bold">{movie?.title}</h1>
                    <p className="text-gray-400">{movie?.year ?? "N/A"} • {movie?.rating ?? "N/A"}/10⭐ </p>
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
                                    </div>
                                </button>
                            ))}
                        </div>
                        {subtitleError && (
                            <div className="mt-2 text-sm text-yellow-400">
                                {subtitleError}
                            </div>
                        )}
                    </div>
                    )}
                    <div className="mt-4 flex items-center gap-4">
                    <button
                        onClick={toggleFavorite}
                        disabled={isButtonDisabled}
                        className={`p-2 rounded-full transition-all duration-200 hover:scale-110 ${
                            isButtonDisabled ? "opacity-50 cursor-not-allowed" : "hover:bg-gray-700"
                        }`}
                        title="Toggle favorite"
                    >
                        <Heart
                            className={`w-6 h-6 transition-colors ${
                                isFavorite ? "fill-red-500 text-red-500" : "fill-transparent text-gray-400"
                            }`}
                        />
                    </button>
                    </div>
                </div>
            </div>

            {hascommented && userComment ? (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold mb-4">{t("movies.comment")}</h2>
                    <div className="bg-gray-700 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
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
                            <div className="flex flex-col items-end gap-2">
                                {!editingUserComment && (
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={handleEditUserComment}
                                            className="text-gray-400 hover:text-blue-500 transition-colors p-1"
                                            title="Edit comment"
                                        >
                                            <Pencil className="h-4 w-4" />
                                        </button>
                                        <button
                                            onClick={handleDeleteUserComment}
                                            className="text-gray-400 hover:text-red-500 transition-colors p-1"
                                            title="Delete comment"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                )}
                                {!editingUserComment ? (
                                    <div className="flex items-center gap-1">
                                        {renderStars(userComment.rating)}
                                        <span className="ml-1 text-sm text-gray-400">
                                            ({userComment.rating}/5)
                                        </span>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-1">
                                        {[1, 2, 3, 4, 5].map((star) => (
                                            <button
                                                key={star}
                                                onClick={() => handleUserCommentInputChange('rating', star)}
                                                className={`transition-colors ${
                                                    star <= editUserCommentText.rating
                                                        ? 'text-yellow-400 hover:text-yellow-300'
                                                        : 'text-gray-400 hover:text-gray-300'
                                                }`}
                                            >
                                                <Star className="h-4 w-4 fill-current" />
                                            </button>
                                        ))}
                                        <span className="ml-1 text-sm text-gray-400">
                                            ({editUserCommentText.rating}/5)
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                        
                        {!editingUserComment ? (
                            <p className="text-gray-200 leading-relaxed">{userComment.comment}</p>
                        ) : (
                            <div>
                                <textarea
                                    id="edit-user-comment"
                                    name="edit-user-comment"
                                    value={editUserCommentText.comment}
                                    onChange={(e) => handleUserCommentInputChange('comment', e.target.value)}
                                    className="w-full p-3 bg-gray-600 text-white rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    rows={3}
                                    placeholder="Write your comment..."
                                    maxLength={1000}
                                />
                                <div className="flex justify-between items-center mt-2">
                                    <div className="text-xs text-gray-400">
                                        {editUserCommentText.comment.length}/1000 {t("movies.character")}
                                    </div>
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={handleSaveEditUserComment}
                                            className="text-gray-400 hover:text-green-500 transition-colors p-1"
                                            title="Save changes"
                                        >
                                            <Check className="h-4 w-4" />
                                        </button>
                                        <button
                                            onClick={handleCancelEditUserComment}
                                            className="text-gray-400 hover:text-red-500 transition-colors p-1"
                                            title="Cancel edit"
                                        >
                                            <X className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>
                                {editUserCommentError && editUserCommentError.length > 0 && (
                                    <div className="mt-2 text-red-500 text-xs">
                                        {editUserCommentError.map((err, index) => (
                                            <p key={index}>{err}</p>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
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
                    <>
                        <h2 className="text-xl font-semibold mb-4">{t("movies.comments")}</h2>
                        {comments.map((comment) => (
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
                        ))}
                    </>
                )}
            </div>
            
            {isStreamingModalOpen && (
                <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50">
                    <div className="bg-gray-800 rounded-lg w-full h-full m-4 relative">
                        <div className="flex items-center justify-between p-4 border-b border-gray-700">
                            <h2 className="text-lg font-semibold">
                                {movie?.title} - {selectedTorrent?.quality}
                            </h2>
                            <button
                                onClick={closeStreamingModal}
                                className="p-1 rounded-full hover:bg-gray-700 transition-colors"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        <div className="flex-1 flex items-center justify-center p-4 md:p-8 lg:p-12 relative bg-gray-900">
                            <div className="relative w-full max-w-7xl">
                                <video
                                    ref={videoRef}
                                    controls
                                    autoPlay
                                    className="w-full max-h-[calc(100vh-16rem)] object-contain bg-black rounded-lg shadow-[0_20px_50px_rgba(0,0,0,0.8)]"
                                />
                                {isPreparingStream && (
                                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm text-center space-y-4 rounded-lg">
                                        <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full" />
                                        <p className="text-lg font-medium text-white">
                                            {t("movies.video.streaming")}
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}