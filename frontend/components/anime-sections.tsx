"use client";

import React from "react";
import Container from "./container";
import AnimeCard from "./anime-card";
import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";

import { IAnime } from "@/types/anime";
import { ROUTES } from "@/constants/routes";

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
    <Container className="flex flex-col gap-6 py-10 items-center lg:items-start">
      {/* HEADER */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="flex items-center justify-between w-full"
      >
        <div className="flex items-center gap-4">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">{props.title}</h2>
          <motion.div
            initial={{ scale: 0 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2, type: "spring" }}
          >
            <span className="px-3 py-1.5 bg-primary/10 text-primary rounded-full text-sm font-semibold border border-primary/20">
              {props.trendingAnime?.length || 0} anime
            </span>
          </motion.div>
        </div>

        <motion.button
          whileHover={{ x: 5 }}
          className="hidden sm:flex items-center gap-2 text-primary hover:text-primary/80 transition-colors group"
        >
          <span className="font-semibold">Показать всё</span>
          <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </motion.button>
      </motion.div>

      {/* GRID */}
      <div className="grid lg:grid-cols-5 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6 2xl:grid-cols-7 w-full gap-4 md:gap-5 content-center">
        {props.trendingAnime.map((anime, idx) => (
          <motion.div
            key={anime.id}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: idx * 0.05, duration: 0.5 }}
          >
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
          </motion.div>
        ))}
      </div>
    </Container>
  );
};

const LoadingSkeleton = () => {
  return (
    <Container className="flex flex-col gap-6 py-10 items-center lg:items-start">
      <div className="h-8 w-64 skeleton rounded-md"></div>
      <div className="grid lg:grid-cols-5 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6 2xl:grid-cols-7 w-full gap-4 md:gap-5 content-center">
        {[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1].map((_, idx) => {
          return (
            <div
              key={idx}
              className="rounded-xl h-[15.625rem] min-w-[10.625rem] max-w-[12.625rem] md:h-[18.75rem] md:max-w-[12.5rem] skeleton"
            ></div>
          );
        })}
      </div>
    </Container>
  );
};

export default AnimeSections;
