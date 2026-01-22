"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";

import { cn } from "@/lib/utils";
import { Badge } from "./ui/badge";
import { Captions, Mic, Star, Play, Heart } from "lucide-react";
import { WatchHistory } from "@/hooks/use-get-bookmark";

type Props = {
  className?: string;
  poster: string;
  title: string;
  episodeCard?: boolean;
  sub?: number | null;
  dub?: number | null;
  subTitle?: string;
  displayDetails?: boolean;
  variant?: "sm" | "lg";
  href?: string;
  showGenre?: boolean;
  watchDetail?: WatchHistory | null;
  continueWatching?: {
    episode: number;
    progressPercent: number;
    isCompleted: boolean;
  } | null;
  rating?: number | null;
  isNew?: boolean;
  isOngoing?: boolean;
};

const AnimeCard = ({
  displayDetails = true,
  // showGenre = true,
  variant = "sm",
  ...props
}: Props) => {
  const safeCurrent =
    typeof props.watchDetail?.current === "number"
      ? props.watchDetail.current
      : 0;
  const safeTotal =
    typeof props.watchDetail?.timestamp === "number" &&
    props.watchDetail.timestamp > 0
      ? props.watchDetail.timestamp
      : 0;

  const clampedCurrent = Math.min(safeCurrent, safeTotal);

  const percentage = safeTotal > 0 ? (clampedCurrent / safeTotal) * 100 : 0;
  const continueWatching = props.continueWatching;

  return (
    <motion.div
      whileHover={{ y: -12, scale: 1.03 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="group relative"
    >
      <Link href={props.href as string}>
        <div
          className={cn([
            "rounded-2xl overflow-hidden relative cursor-pointer bg-card/50 backdrop-blur-sm",
            variant === "sm" &&
              "h-[12rem] min-[320px]:h-[16.625rem] sm:h-[18rem] max-w-[12.625rem] md:min-w-[12rem]",
            variant === "lg" &&
              "max-w-[12.625rem] md:max-w-[18.75rem] h-auto md:h-[25rem] shrink-0 lg:w-[18.75rem]",
            props.className,
          ])}
        >
          {/* Image with aspect ratio 2:3 */}
          <div className="relative w-full h-full">
            <Image
              src={props.poster}
              alt={props.title}
              fill
              className="object-cover transition-transform duration-700 group-hover:scale-125"
              unoptimized
            />
            
            {/* Gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent opacity-60 group-hover:opacity-90 transition-opacity duration-500"></div>
            
            {/* SUB/DUB Badges at top left */}
            <div className="absolute top-3 left-3 flex gap-2 z-10">
              {props.sub && (
                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  className="bg-blue-500/90 backdrop-blur-sm px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1"
                >
                  <Captions className="w-3 h-3" />
                  SUB {props.sub}
                </motion.div>
              )}
              {props.dub && (
                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.1 }}
                  className="bg-green-500/90 backdrop-blur-sm px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1"
                >
                  <Mic className="w-3 h-3" />
                  DUB {props.dub}
                </motion.div>
              )}
            </div>

            {/* Status Badges at top */}
            {(props.isNew || props.isOngoing) && (
              <div className="absolute top-3 left-3 flex flex-wrap gap-1.5 z-10">
                {props.isNew && (
                  <Badge className="bg-primary text-primary-foreground text-xs font-semibold px-2 py-0.5">
                    Новинка
                  </Badge>
                )}
                {props.isOngoing && (
                  <Badge className="bg-green-500 text-white text-xs font-semibold px-2 py-0.5">
                    Онгоинг
                  </Badge>
                )}
              </div>
            )}

            {/* Rating - always visible */}
            {props.rating && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="absolute top-3 right-3 flex items-center gap-1.5 bg-black/70 backdrop-blur-md px-3 py-1.5 rounded-full border border-yellow-500/30 z-10"
              >
                <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                <span className="text-sm font-bold text-white">{props.rating.toFixed(1)}</span>
              </motion.div>
            )}

            {/* PLAY BUTTON - appears on hover */}
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-20"
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className="w-16 h-16 md:w-20 md:h-20 rounded-full bg-primary/90 backdrop-blur-md flex items-center justify-center shadow-2xl shadow-primary/50 border-2 border-white/20"
              >
                <Play className="w-8 h-8 md:w-10 md:h-10 fill-white text-white ml-1" />
              </motion.div>
            </motion.div>
          </div>

        {displayDetails && (
          <>
            {/* INFO SECTION - slide up on hover */}
            <motion.div
              initial={{ y: 0 }}
              className="absolute bottom-0 left-0 right-0 p-4 z-10"
            >
              <div className="transform translate-y-8 group-hover:translate-y-0 transition-transform duration-500">
                <h3 className="font-bold text-white text-sm md:text-base line-clamp-2 mb-2 drop-shadow-lg">
                  {props.title}
                </h3>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-gray-200">
                    {props.subTitle && (
                      <>
                        <span className="px-2 py-0.5 bg-white/20 rounded-md backdrop-blur-sm">{props.subTitle}</span>
                        <span>•</span>
                      </>
                    )}
                    {continueWatching && (
                      <span>Ep {continueWatching.episode}</span>
                    )}
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.2 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-2 bg-white/20 backdrop-blur-sm rounded-full"
                  >
                    <Heart className="w-4 h-4 text-white" />
                  </motion.button>
                </div>
              </div>
            </motion.div>

            {/* PROGRESS BAR for continue watching */}
            {continueWatching && !continueWatching.isCompleted && (
              <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gray-800/80 z-10">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${continueWatching.progressPercent}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="h-full bg-gradient-to-r from-primary via-pink-500 to-primary rounded-full"
                />
              </div>
            )}

            {/* PROGRESS BAR for watch detail */}
            {props.watchDetail && !continueWatching && (
              <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gray-800/80 z-10">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="h-full bg-gradient-to-r from-primary via-pink-500 to-primary rounded-full"
                />
              </div>
            )}
          </>
        )}
        </div>
      </Link>
    </motion.div>
  );
};

export default AnimeCard;
