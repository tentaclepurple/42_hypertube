export interface Torrent {
  quality: string;
  size?: string;
  hash?: string;
  seeds?: number;
  peers?: number;
  url?: string;
  type?: string;
  video_codec?: string;
  audio_channel?: string;
}

export interface Movie {
    id: string;
    imdb_id: string;
    title: string;
    year: number;
    rating: number;
    runtime: number;
    genres: string[];
    summary: string;
    poster: string;
    director?: string[];
    cast?: string[];
    torrents?: Torrent[];
    torrent_hash?: string;
    download_status?: string;
    download_progress?: number;
    view_percentage?: number;
    completed?: boolean;
    hypertube_rating?: number;
  }