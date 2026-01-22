"use client";

import {
  Carousel,
  CarouselApi,
  CarouselContent,
  CarouselItem,
} from "./ui/carousel";

import Container from "./container";
import { motion } from "framer-motion";

import React, { useState, useEffect } from "react";
import { ArrowLeft, ArrowRight, Play, Info, Calendar, Flame, Heart } from "lucide-react";

import { ROUTES } from "@/constants/routes";
import { ButtonLink } from "./common/button-link";
import { SpotlightAnime } from "@/types/anime";
import { HERO_SPOTLIGHT_FALLBACK } from "@/constants/fallbacks";
import { cn } from "@/lib/utils";

type IHeroSectionProps = {
  spotlightAnime: SpotlightAnime[];
  isDataLoading: boolean;
};

const HeroSection = (props: IHeroSectionProps) => {
  const [api, setApi] = React.useState<CarouselApi>();
  const [current, setCurrent] = useState(0);

  const hasSpotlight = Array.isArray(props.spotlightAnime) && props.spotlightAnime.length > 0;
  const shouldUseFallback = props.isDataLoading || !hasSpotlight;
  const spotlightList = shouldUseFallback ? HERO_SPOTLIGHT_FALLBACK : props.spotlightAnime;

  // Auto-play every 5 seconds
  useEffect(() => {
    if (!api) return;
    
    const interval = setInterval(() => {
      api.scrollNext();
    }, 5000);

    const handleSelect = () => {
      setCurrent(api.selectedScrollSnap());
    };

    api.on("select", handleSelect);

    return () => {
      clearInterval(interval);
      api.off("select", handleSelect);
    };
  }, [api]);

  if (!spotlightList.length) return <LoadingSkeleton />;

  return (
    <div className="relative h-[85vh] w-full overflow-hidden">
      <Carousel className="w-full" setApi={setApi} opts={{ loop: true }}>
        <CarouselContent className="">
          {spotlightList.map((anime, index) => (
            <CarouselItem key={index}>
              <HeroCarouselItem anime={anime} isActive={current === index} />
            </CarouselItem>
          ))}
        </CarouselContent>
      </Carousel>

      {/* DOT NAVIGATION */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex gap-3 z-50">
        {spotlightList.map((_, i) => (
          <motion.button
            key={i}
            onClick={() => api?.scrollTo(i)}
            className={cn(
              "h-1.5 rounded-full transition-all duration-500",
              i === current 
                ? "w-12 bg-primary shadow-lg shadow-primary/50" 
                : "w-8 bg-white/30 hover:bg-white/50"
            )}
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.9 }}
          />
        ))}
      </div>

      {/* ARROW BUTTONS */}
      <div className="absolute right-8 bottom-8 flex gap-4 z-50">
        <motion.button
          whileHover={{ scale: 1.1, x: -5 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => api?.scrollPrev()}
          className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-xl border border-white/20 flex items-center justify-center hover:bg-primary/20 transition-all duration-300"
        >
          <ArrowLeft className="w-6 h-6 text-white" />
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.1, x: 5 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => api?.scrollNext()}
          className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-xl border border-white/20 flex items-center justify-center hover:bg-primary/20 transition-all duration-300"
        >
          <ArrowRight className="w-6 h-6 text-white" />
        </motion.button>
      </div>
    </div>
  );
};

const HeroCarouselItem = ({ anime, isActive }: { anime: SpotlightAnime; isActive?: boolean }) => {
  return (
    <div className="relative h-[85vh] w-full overflow-hidden">
      {/* BACKGROUND IMAGE with parallax */}
      <motion.div
        initial={{ scale: 1.1 }}
        animate={{ scale: isActive ? 1 : 1.1 }}
        transition={{ duration: 8, ease: "easeOut" }}
        className="absolute inset-0 bg-cover bg-no-repeat bg-center"
        style={{ backgroundImage: `url(${anime?.poster})` }}
      />

      {/* GRADIENT OVERLAYS */}
      <div className="absolute inset-0 bg-gradient-to-r from-black via-black/70 to-transparent"></div>
      <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>

      {/* CONTENT */}
      <Container className="relative h-full flex items-center z-20">
        <motion.div
          initial={{ opacity: 0, x: -100 }}
          animate={{ opacity: isActive ? 1 : 0, x: isActive ? 0 : -100 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="max-w-2xl space-y-6"
        >
          {/* RANK BADGE */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex items-center gap-3"
          >
            {anime.rank && (
              <div className="flex items-center gap-2 bg-yellow-500/20 backdrop-blur-md px-4 py-2 rounded-full border border-yellow-500/30">
                <Flame className="w-5 h-5 text-yellow-500" />
                <span className="font-bold text-yellow-500">#{anime.rank} Trending</span>
              </div>
            )}
          </motion.div>

          {/* TITLE */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-5xl md:text-6xl lg:text-7xl font-black tracking-tight leading-none"
          >
            {anime?.name}
          </motion.h1>

          {/* METADATA */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="flex flex-wrap gap-3 items-center text-sm"
          >
            <span className="px-3 py-1.5 bg-primary/20 rounded-full font-semibold">
              {anime?.type || "TV Series"}
            </span>
            {anime?.otherInfo?.[0] && (
              <>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {anime.otherInfo[0]}
                </span>
              </>
            )}
            {anime.episodes.sub && (
              <>
                <span>•</span>
                <span className="px-2 py-1 bg-blue-500/20 rounded text-blue-300">SUB {anime.episodes.sub}</span>
              </>
            )}
            {anime.episodes.dub && (
              <>
                <span>•</span>
                <span className="px-2 py-1 bg-green-500/20 rounded text-green-300">DUB {anime.episodes.dub}</span>
              </>
            )}
          </motion.div>

          {/* DESCRIPTION */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-base md:text-lg text-gray-300 line-clamp-3 md:line-clamp-4 max-w-xl leading-relaxed"
          >
            {anime?.description}
          </motion.p>

          {/* ACTION BUTTONS */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="flex items-center gap-4 pt-4"
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <ButtonLink
                href={`${ROUTES.ANIME_DETAILS}/${anime.id}`}
                className="flex items-center gap-3 bg-primary hover:bg-primary/90 px-8 py-4 h-14 text-lg font-bold shadow-2xl shadow-primary/30 transition-all rounded-2xl"
              >
                <Play className="w-6 h-6 fill-white" />
                Смотреть
              </ButtonLink>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <ButtonLink
                href={`${ROUTES.ANIME_DETAILS}/${anime.id}`}
                className="flex items-center gap-3 bg-white/10 backdrop-blur-md hover:bg-white/20 px-8 py-4 h-14 text-lg font-bold border border-white/20 transition-all rounded-2xl"
                variant="outline"
              >
                <Info className="w-6 h-6" />
                Подробнее
              </ButtonLink>
            </motion.div>
            <motion.button
              whileHover={{ scale: 1.1, rotate: 5 }}
              whileTap={{ scale: 0.9 }}
              className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center hover:bg-primary/20 transition-all"
            >
              <Heart className="w-6 h-6" />
            </motion.button>
          </motion.div>
        </motion.div>
      </Container>
    </div>
  );
};

const LoadingSkeleton = () => {
  return (
    <div className="h-[80vh] w-full relative">
      <div className="w-full h-[calc(100%-5.25rem)] mt-[5.25rem] relative z-20">
        <Container className="w-full h-full flex flex-col justify-end md:justify-center pb-10">
          <div className="space-y-2 lg:w-[40vw]">
            <div className="h-16 animate-pulse bg-slate-700 w-[75%]"></div>
            <div className="h-40 animate-pulse w-full bg-slate-700"></div>
            <div className="flex items-center gap-5">
              <span className="h-10 w-[7.5rem] animate-pulse bg-slate-700"></span>
              <span className="h-10 w-[7.5rem] animate-pulse bg-slate-700"></span>
            </div>
          </div>
        </Container>
      </div>
      <div className="absolute hidden md:flex items-center gap-5 right-10 bottom-32 z-50 isolate">
        <span className="h-10 w-10 rounded-full animate-pulse bg-slate-700"></span>
        <span className="h-10 w-10 rounded-full animate-pulse bg-slate-700"></span>
      </div>
    </div>
  );
};
export default HeroSection;
