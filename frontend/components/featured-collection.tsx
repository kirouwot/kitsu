import React from "react";
import Container from "./container";
import { IAnime, LatestCompletedAnime } from "@/types/anime";
import { MIN_FEATURED_ANIME } from "@/constants/ui";
import Image from "next/image";
import { Button } from "./ui/button";
import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { ROUTES } from "@/constants/routes";

type Props = {
  featuredAnime: [
    mostFavorite: { title: string; anime: IAnime[] },
    mostPopular: { title: string; anime: IAnime[] },
    latestCompleted: { title: string; anime: LatestCompletedAnime[] }
  ];
  loading: boolean;
};

const FeaturedCollection = ({ featuredAnime, loading }: Props) => {
  const PLACEHOLDER_CARD_CLASS =
    "rounded-2xl h-[25rem] w-[100%] animate-pulse bg-slate-700";
  const hasEnoughAnime = (category: { anime: IAnime[] }) =>
    Array.isArray(category.anime) &&
    category.anime.length >= MIN_FEATURED_ANIME;

  const hasRenderableCategory =
    Array.isArray(featuredAnime) && featuredAnime.some(hasEnoughAnime);

  const shouldShowSkeleton = loading || !featuredAnime || !hasRenderableCategory;

  if (shouldShowSkeleton) return <LoadingSkeleton />;
  return (
    <Container className="flex flex-col gap-6 items-center lg:items-start py-12">
      <h2 className="text-2xl md:text-3xl font-bold">Подборки</h2>
      <div className="grid w-full gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {featuredAnime.map((category, idx) =>
          hasEnoughAnime(category) ? (
            <FeaturedCollectionCard
              title={category.title}
              key={idx}
              anime={category.anime}
            />
          ) : (
            <div
              key={`placeholder-${idx}`}
              className={PLACEHOLDER_CARD_CLASS}
            />
          ),
        )}
      </div>
    </Container>
  );
};

const FeaturedCollectionCard = ({ title, anime }: { title: string; anime: IAnime[] }) => {
  if (!anime || anime.length < 3) return null;
  
  return (
    <Link href={ROUTES.HOME}>
      <div className="group relative h-[25rem] rounded-2xl overflow-hidden cursor-pointer">
        {/* Background из 3х постеров */}
        <div className="absolute inset-0 grid grid-cols-3 gap-1">
          {anime.slice(0, 3).map((a) => (
            <div key={a.id} className="relative w-full h-full">
              <Image 
                src={a.poster} 
                alt={a.name}
                fill 
                className="object-cover" 
                unoptimized
              />
            </div>
          ))}
        </div>
        
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-black/20 group-hover:via-black/80 transition-colors duration-300" />
        
        {/* Content */}
        <div className="absolute inset-0 flex flex-col justify-end p-8">
          <h3 className="text-2xl font-bold mb-2">{title}</h3>
          <p className="text-gray-300 mb-4">{anime.length} аниме</p>
          
          <Button className="w-fit gap-2 bg-primary hover:bg-primary/90">
            Смотреть
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Link>
  );
};

const LoadingSkeleton = () => {
  return (
    <Container className="flex flex-col gap-6 py-12 items-center lg:items-start">
      <div className="h-10 w-[15.625rem] animate-pulse bg-slate-700 rounded-lg"></div>
      <div className="grid w-full gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 1, 1].map((_, idx) => {
          return (
            <div
              key={idx}
              className="rounded-2xl h-[25rem] w-[100%] animate-pulse bg-slate-700"
            ></div>
          );
        })}
      </div>
    </Container>
  );
};

export default FeaturedCollection;
