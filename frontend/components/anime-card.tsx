import React from "react";
import Link from "next/link";
import Image from "next/image";

import { cn, formatSecondsToMMSS } from "@/lib/utils";
import { Badge } from "./ui/badge";
import { buttonVariants } from "./ui/button";
import { Captions, Mic, Play } from "lucide-react";
import { WatchHistory } from "@/hooks/use-get-bookmark";
import { Progress } from "./ui/progress";
import { motion } from "framer-motion";

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
      whileHover={{ y: -8, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="group relative"
    >
      <Link href={props.href as string}>
        <div
          className={cn([
            "rounded-2xl overflow-hidden relative cursor-pointer",
            variant === "sm" &&
              "h-[12rem] min-[320px]:h-[16.625rem] sm:h-[18rem] max-w-[12.625rem] md:min-w-[12rem]",
            variant === "lg" &&
              "max-w-[12.625rem] md:max-w-[18.75rem] h-auto md:h-[25rem] shrink-0 lg:w-[18.75rem]",
            props.className,
          ])}
        >
          <Image
            src={props.poster}
            alt={props.title}
            height={100}
            width={100}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
            unoptimized
          />

          {/* ГРАДИЕНТ снизу */}
          <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

          {displayDetails && (
            <>
              {/* СТАТУСЫ вверху */}
              {props.episodeCard && (
                <div className="absolute top-3 left-3 flex gap-2 z-10">
                  {props.sub && (
                    <Badge className="bg-blue-500/90 backdrop-blur-sm flex items-center gap-1">
                      <Captions className="w-3 h-3" />
                      <span>{props.sub}</span>
                    </Badge>
                  )}
                  {props.dub && (
                    <Badge className="bg-green-500/90 backdrop-blur-sm flex items-center gap-1">
                      <Mic className="w-3 h-3" />
                      <span>{props.dub}</span>
                    </Badge>
                  )}
                </div>
              )}

              {/* КНОПКА PLAY при hover */}
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10">
                <div className="w-16 h-16 rounded-full bg-primary/90 backdrop-blur-sm flex items-center justify-center">
                  <Play className="w-8 h-8 fill-white text-white" />
                </div>
              </div>

              {/* INFO внизу */}
              <div className="absolute bottom-0 left-0 right-0 p-4">
                <div className="absolute inset-0 bg-gradient-to-t from-black to-transparent -z-10"></div>
                
                {continueWatching ? (
                  <div className="flex flex-col gap-1 relative z-10">
                    <h5 className="line-clamp-1 font-semibold text-white">{props.title}</h5>
                    <p className="text-xs text-gray-300">
                      Episode {continueWatching.episode}
                    </p>
                    {continueWatching.isCompleted ? (
                      <span className="text-xs font-semibold text-emerald-400">
                        Completed
                      </span>
                    ) : (
                      <Progress value={continueWatching.progressPercent} />
                    )}
                    <span
                      className={cn(
                        buttonVariants({ variant: "secondary", size: "sm" }),
                        "mt-1 w-fit text-xs pointer-events-none",
                      )}
                    >
                      Continue
                    </span>
                  </div>
                ) : (
                  <>
                    <h5 className="line-clamp-1 font-semibold text-white relative z-10">{props.title}</h5>
                    {props.watchDetail && (
                      <div className="relative z-10">
                        <p className="text-xs text-gray-400">
                          Episode {props.watchDetail.episodeNumber} -
                          {formatSecondsToMMSS(props.watchDetail.current)} /
                          {formatSecondsToMMSS(props.watchDetail.timestamp)}
                        </p>
                        <Progress value={percentage} />
                      </div>
                    )}
                    {!props.watchDetail && props.subTitle && (
                      <p className="text-sm text-gray-400 relative z-10">{props.subTitle}</p>
                    )}
                  </>
                )}
              </div>
            </>
          )}
        </div>

        {/* НАЗВАНИЕ под карточкой (если есть continueWatching, дублируется выше) */}
        {displayDetails && !continueWatching && (
          <div className="mt-3 space-y-1">
            <h3 className="font-semibold text-sm line-clamp-2 group-hover:text-primary transition-colors">
              {props.title}
            </h3>
            {props.subTitle && (
              <p className="text-xs text-muted-foreground">
                {props.subTitle}
              </p>
            )}
          </div>
        )}
      </Link>
    </motion.div>
  );
};

export default AnimeCard;
