import { Star } from "lucide-react";

export const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

export const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, index) => (
        <Star 
            key={index} 
            className={`h-4 w-4 ${
                index < rating ? "fill-yellow-400 text-yellow-400" : "text-gray-400"
            }`} 
        />
    ));
};