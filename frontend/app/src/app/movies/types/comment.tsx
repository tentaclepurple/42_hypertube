export interface Comment {
    id: string;
    comment: string;
    rating: number;
    username: string;
    created_at: string;
    user_id: string;
    movie_id?: string;
    movie_title?: string;
}