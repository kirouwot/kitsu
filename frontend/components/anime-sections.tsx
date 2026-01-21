"use client";

import React from "react";
import Container from "./container";
import AnimeCard from "./anime-card";

import BlurFade from "./ui/blur-fade";
import { IAnime } from "@/types/anime";
import { ROUTES } from "@/constants/routes";
import { Button } from "./ui/button";
import { ChevronRight } from "lucide-react";
import { Badge } from "./ui/badge";

type Props = {
  trendingAnime: IAnime[];
  loading: boolean;
  title: string;
};

const AnimeSections = (props: Props) => {
  if (props.loading) return <LoadingSkeleton />;
  if (!Array.isArray(props.trendingAnime) || props.trendingAnime.length === 0) {
    return <LoadingSkeleton />;
  }
  return (
    <Container className="flex flex-col gap-5 py-12 items-center lg:items-start">
      {/* HEADER секции */}
      <div className="flex items-center justify-between w-full mb-3">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl md:text-3xl font-bold">{props.title}</h2>
          <Badge variant="secondary" className="text-xs hidden sm:inline-flex">
            {props.trendingAnime.length} аниме
          </Badge>
        </div>
        
        <Button variant="ghost" className="gap-2 group">
          Показать все
          <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </Button>
      </div>

      {/* GRID с правильными breakpoints */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 w-full gap-6">
        {props.trendingAnime.map((anime, idx) => (
          <BlurFade key={idx} delay={idx * 0.05} inView>
            <AnimeCard
              title={anime.name}
              subTitle={anime.type ? anime.type : `Rank: ${anime.rank}`}
              poster={anime.poster}
              className="self-center justify-self-center"
              href={`${ROUTES.ANIME_DETAILS}/${anime.id}`}
              episodeCard
              sub={anime?.episodes?.sub}
              dub={anime?.episodes?.dub}
            />
          </BlurFade>
        ))}
      </div>
    </Container>
  );
};

const LoadingSkeleton = () => {
  return (
    <Container className="flex flex-col gap-5 py-12 items-center lg:items-start">
      <div className="flex items-center justify-between w-full mb-3">
        <div className="flex items-center gap-4">
          <div className="h-10 w-[15.625rem] animate-pulse bg-slate-700 rounded-lg"></div>
          <div className="h-6 w-20 animate-pulse bg-slate-700 rounded-full"></div>
        </div>
        <div className="h-10 w-32 animate-pulse bg-slate-700 rounded-lg"></div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 w-full gap-6">
        {[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1].map((_, idx) => {
          return (
            <div
              key={idx}
              className="rounded-2xl h-[15.625rem] min-w-[10.625rem] max-w-[12.625rem] md:h-[18.75rem] md:max-w-[12.5rem] animate-pulse bg-slate-700"
            ></div>
          );
        })}
      </div>
    </Container>
  );
};

export default AnimeSections;
