"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { Flame, ArrowRight } from "lucide-react";
import { IAnime } from "@/types/anime";
import { ROUTES } from "@/constants/routes";

type Props = {
  title: string;
  anime: IAnime[];
};

const FeaturedCollectionCard = (props: Props) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      whileHover={{ y: -8, scale: 1.02 }}
      className="group relative h-[400px] rounded-2xl overflow-hidden cursor-pointer"
    >
      <Link href={`${ROUTES.ANIME_DETAILS}/${props.anime[0].id}`}>
        {/* TRIPLE POSTER BLEND */}
        <div className="absolute inset-0 grid grid-cols-3 gap-1">
          {props.anime.slice(0, 3).map((a, i) => (
            <div key={i} className="relative">
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

        {/* GRADIENT OVERLAY */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/70 to-black/30 group-hover:via-black/90 transition-all duration-500" />

        {/* CONTENT */}
        <div className="absolute inset-0 flex flex-col justify-end p-8">
          <motion.div
            initial={{ y: 20 }}
            whileInView={{ y: 0 }}
            className="flex items-center gap-2 mb-3"
          >
            <Flame className="w-5 h-5 text-primary" />
            <span className="text-sm font-semibold text-primary">{props.anime.length} Anime</span>
          </motion.div>

          <h3 className="text-3xl font-bold mb-4 group-hover:text-primary transition-colors">
            {props.title}
          </h3>

          <motion.button
            whileHover={{ x: 5 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center gap-2 w-fit px-6 py-3 bg-primary rounded-xl font-semibold group-hover:shadow-lg group-hover:shadow-primary/50 transition-all"
          >
            Обзор
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </motion.button>
        </div>

        {/* GLOW EFFECT */}
        <div className="absolute -inset-1 bg-gradient-to-r from-primary via-pink-500 to-primary opacity-0 group-hover:opacity-20 blur-2xl transition-opacity duration-500" />
      </Link>
    </motion.div>
  );
};

export default FeaturedCollectionCard;
