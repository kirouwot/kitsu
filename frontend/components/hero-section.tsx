"use client";

import {
  Carousel,
  CarouselApi,
  CarouselContent,
  CarouselItem,
} from "./ui/carousel";

import Container from "./container";
import { Button } from "./ui/button";

import React from "react";
import { Info, Play, Heart, Star, Captions, Mic } from "lucide-react";

import { ROUTES } from "@/constants/routes";
import { ButtonLink } from "./common/button-link";
import { SpotlightAnime } from "@/types/anime";
import { Badge } from "./ui/badge";
import { HERO_SPOTLIGHT_FALLBACK } from "@/constants/fallbacks";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

type IHeroSectionProps = {
  spotlightAnime: SpotlightAnime[];
  isDataLoading: boolean;
};

const HeroSection = (props: IHeroSectionProps) => {
  const [api, setApi] = React.useState<CarouselApi>();
  const [current, setCurrent] = React.useState(0);

  const hasSpotlight = Array.isArray(props.spotlightAnime) && props.spotlightAnime.length > 0;
  const shouldUseFallback = props.isDataLoading || !hasSpotlight;
  const spotlightList = shouldUseFallback ? HERO_SPOTLIGHT_FALLBACK : props.spotlightAnime;
  
  React.useEffect(() => {
    if (!api) return;

    setCurrent(api.selectedScrollSnap());

    api.on("select", () => {
      setCurrent(api.selectedScrollSnap());
    });
  }, [api]);

  if (!spotlightList.length) return <LoadingSkeleton />;

  return (
    <div className="relative h-[85vh] w-full overflow-hidden">
      <Carousel className="w-full h-full" setApi={setApi} opts={{}}>
        <CarouselContent className="h-full">
          {spotlightList.map((anime, index) => (
            <CarouselItem key={index} className="h-full">
              <HeroCarouselItem anime={anime} />
            </CarouselItem>
          ))}
        </CarouselContent>
      </Carousel>

      {/* Навигация карусели */}
      <div className="absolute bottom-8 right-8 flex gap-3 z-50">
        {spotlightList.map((_, i) => (
          <button
            key={i}
            onClick={() => api?.scrollTo(i)}
            className={cn(
              "h-1 rounded-full transition-all",
              i === current ? "w-12 bg-primary" : "w-8 bg-white/30 hover:bg-white/50"
            )}
          />
        ))}
      </div>
    </div>
  );
};

const HeroCarouselItem = ({ anime }: { anime: SpotlightAnime }) => {
  return (
    <div className="relative h-full w-full">
      {/* BACKGROUND с эффектами */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${anime?.poster})` }}
      />

      {/* Blur overlay для глубины */}
      <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-r from-background via-transparent to-transparent" />

      {/* CONTENT */}
      <Container className="relative h-full flex items-center">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-2xl space-y-6"
        >
          {/* Рейтинг + Тип + Эпизоды */}
          <div className="flex items-center gap-3 text-sm flex-wrap">
            {anime.rank && (
              <div className="flex items-center gap-2 bg-yellow-500/20 px-3 py-1 rounded-full backdrop-blur-sm">
                <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                <span className="font-bold">{anime.rank}</span>
              </div>
            )}
            {anime.episodes.sub && (
              <Badge className="bg-blue-500/90 backdrop-blur-sm flex items-center gap-1">
                <Captions className="w-3 h-3" />
                <span>{anime.episodes.sub} эп</span>
              </Badge>
            )}
            {anime.episodes.dub && (
              <Badge className="bg-green-500/90 backdrop-blur-sm flex items-center gap-1">
                <Mic className="w-3 h-3" />
                <span>{anime.episodes.dub} эп</span>
              </Badge>
            )}
            {anime.type && <Badge variant="secondary">{anime.type}</Badge>}
          </div>

          {/* Название БОЛЬШОЕ */}
          <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-tight">
            {anime?.name}
          </h1>

          {/* Описание с градиентом обрезки */}
          <p className="text-base md:text-lg text-muted-foreground line-clamp-3">
            {anime?.description}
          </p>

          {/* КНОПКИ СОВРЕМЕННЫЕ */}
          <div className="flex items-center gap-4 pt-4 flex-wrap">
            <ButtonLink
              href={`${ROUTES.ANIME_DETAILS}/${anime.id}`}
              className="gap-2 bg-primary hover:bg-primary/90 h-12 md:h-14 px-6 md:px-8 text-base md:text-lg rounded-xl"
            >
              <Info className="w-5 h-5" />
              Подробнее
            </ButtonLink>
            <Button
              size="lg"
              variant="outline"
              className="gap-2 h-12 md:h-14 px-6 md:px-8 text-base md:text-lg rounded-xl backdrop-blur-sm"
            >
              <Play className="w-5 h-5" fill="currentColor" />
              Смотреть
            </Button>
            <Button
              size="lg"
              variant="ghost"
              className="h-12 md:h-14 w-12 md:w-14 rounded-full hover:bg-primary/20"
            >
              <Heart className="w-6 h-6" />
            </Button>
          </div>
        </motion.div>
      </Container>
    </div>
  );
};

const LoadingSkeleton = () => {
  return (
    <div className="h-[85vh] w-full relative">
      <div className="w-full h-full relative z-20">
        <Container className="w-full h-full flex items-center pb-10">
          <div className="space-y-6 max-w-2xl">
            <div className="flex items-center gap-3">
              <div className="h-8 w-24 animate-pulse bg-slate-700 rounded-full"></div>
              <div className="h-8 w-20 animate-pulse bg-slate-700 rounded-full"></div>
            </div>
            <div className="h-16 md:h-20 animate-pulse bg-slate-700 w-[85%] rounded-lg"></div>
            <div className="h-24 animate-pulse w-full bg-slate-700 rounded-lg"></div>
            <div className="flex items-center gap-4">
              <span className="h-14 w-40 animate-pulse bg-slate-700 rounded-xl"></span>
              <span className="h-14 w-32 animate-pulse bg-slate-700 rounded-xl"></span>
            </div>
          </div>
        </Container>
      </div>
      <div className="absolute bottom-8 right-8 flex gap-3 z-50">
        <span className="h-1 w-12 rounded-full animate-pulse bg-slate-700"></span>
        <span className="h-1 w-8 rounded-full animate-pulse bg-slate-700"></span>
        <span className="h-1 w-8 rounded-full animate-pulse bg-slate-700"></span>
      </div>
    </div>
  );
};

export default HeroSection;
