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
    torrents?: any[];
    torrent_hash?: string;
    download_status?: string;
    download_progress?: number;
  }