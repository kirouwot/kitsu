"use client";

import React, { useCallback, useEffect, useState } from "react";
import Container from "./container";
import AnimeCard from "./anime-card";
import { ROUTES } from "@/constants/routes";
import { History } from "lucide-react";
import { motion } from "framer-motion";
import { useAuthSelector } from "@/store/auth-store";
import { api } from "@/lib/api";
import { PLACEHOLDER_POSTER } from "@/utils/constants";
import { getLocalStorageJSON, removeLocalStorageItem } from "@/utils/storage";
import { getPlayerStorage } from "@/utils/player-storage";
import {
  COMPLETED_PROGRESS_MIN,
  CONTINUE_PROGRESS_MAX,
  CONTINUE_PROGRESS_MIN,
  convertFractionToPercent,
  parseNumber,
} from "@/utils/player-progress";

type ContinueWatchingResponse = {
  anime_id: string;
  episode: number;
  progress_percent?: number | null;
};

type BackendAnime = {
  id: string;
  title: string;
  poster?: string | null;
};

type ContinueWatchingItem = {
  id: string;
  title: string;
  poster: string; // Always non-null due to PLACEHOLDER_POSTER fallback
  episode: number;
  progressPercent: number;
  isCompleted: boolean;
};

const MOBILE_LIMIT = 4;
const DESKTOP_LIMIT = 8;
const MOBILE_QUERY = "(max-width: 640px)";

const resolveProgress = (value: unknown) => {
  const normalized = convertFractionToPercent(parseNumber(value));
  if (normalized !== undefined && normalized >= COMPLETED_PROGRESS_MIN) {
    return { isCompleted: true, progressPercent: CONTINUE_PROGRESS_MAX };
  }
  const clamped = Math.min(
    Math.max(normalized ?? CONTINUE_PROGRESS_MIN, CONTINUE_PROGRESS_MIN),
    CONTINUE_PROGRESS_MAX,
  );
  return { isCompleted: false, progressPercent: clamped };
};

const ContinueWatching = () => {
  const [anime, setAnime] = useState<ContinueWatchingItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [displayLimit, setDisplayLimit] = useState(DESKTOP_LIMIT);

  const auth = useAuthSelector((state) => state.auth);
  const isAuthenticated = Boolean(auth?.accessToken);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mediaQuery = window.matchMedia(MOBILE_QUERY);
    const updateLimit = () =>
      setDisplayLimit(mediaQuery.matches ? MOBILE_LIMIT : DESKTOP_LIMIT);
    updateLimit();
    mediaQuery.addEventListener("change", updateLimit);
    return () => mediaQuery.removeEventListener("change", updateLimit);
  }, []);

  const loadContinueWatching = useCallback(
    async (shouldPreserve = false) => {
      if (typeof window === "undefined") return;
      let resolved: ContinueWatchingItem[] = [];
      if (!shouldPreserve) {
        setAnime([]);
      }
      setIsLoading(true);

      if (isAuthenticated) {
        const response = await api.get<ContinueWatchingResponse[]>(
          "/watch/continue",
          { params: { limit: displayLimit } },
        );
        const items = response.data;
        const detailed = await Promise.all(
          items.map(async (item) => {
            const animeResponse = await api.get<BackendAnime>(
              `/anime/${item.anime_id}`,
            );
            return { item, anime: animeResponse.data };
          }),
        );

        resolved = detailed.map(({ item, anime }) => {
          const { progressPercent, isCompleted } = resolveProgress(
            item.progress_percent,
          );
          return {
            id: item.anime_id,
            title: anime.title,
            // Fallback to placeholder for missing posters (UI concern, not API contract violation)
            poster: anime.poster || PLACEHOLDER_POSTER,
            episode: item.episode,
            progressPercent,
            isCompleted,
          };
        });
      } else {
        const watchedAnimes: {
          anime: { id: string; title: string; poster: string };
          episodes: string[];
        }[] = getLocalStorageJSON("watched", []);

        if (!Array.isArray(watchedAnimes)) {
          removeLocalStorageItem("watched");
          resolved = [];
        } else {
          resolved = [...watchedAnimes]
            .reverse()
            .slice(0, displayLimit)
            .map((ani) => {
              const lastEpisode =
                ani.episodes.length > 0
                  ? ani.episodes[ani.episodes.length - 1]
                  : undefined;
              const episodeNumber = parseNumber(lastEpisode);
              if (!episodeNumber) return null;
              const { progressPercent, isCompleted } = resolveProgress(
                getPlayerStorage(ani.anime.id).progressPercent,
              );
              return {
                id: ani.anime.id,
                title: ani.anime.title,
                poster: ani.anime.poster,
                episode: episodeNumber,
                progressPercent,
                isCompleted,
              };
            })
            .filter(Boolean) as ContinueWatchingItem[];
        }
      }

      setAnime(resolved);
      setIsLoading(false);
    },
    [displayLimit, isAuthenticated],
  );

  useEffect(() => {
    void loadContinueWatching();
  }, [loadContinueWatching]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!isAuthenticated) return;
    const handleFocus = () => {
      void loadContinueWatching(true);
    };
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [isAuthenticated, loadContinueWatching]);

  if (isLoading && !anime.length) return null;
  if (!anime.length) return null;

  return (
    <section className="py-8 bg-card/30 backdrop-blur-sm">
      <Container className="flex flex-col gap-5 items-center lg:items-start">
        <motion.h2
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="text-2xl md:text-3xl font-bold flex items-center gap-3"
        >
          <History className="w-6 h-6 text-primary" />
          Continue Watching
        </motion.h2>
        <div className="grid lg:grid-cols-5 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6 2xl:grid-cols-7 w-full gap-5 content-center">
          {anime?.map(
            (ani, idx) =>
              ani.episode && (
                <motion.div
                  key={ani.id ?? idx}
                  initial={{ opacity: 0, x: 50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <AnimeCard
                    title={ani.title}
                    poster={ani.poster}
                    className="self-center justify-self-center"
                    href={`${ROUTES.ANIME_DETAILS}/${ani.id}`}
                    watchDetail={null}
                    continueWatching={{
                      episode: ani.episode,
                      progressPercent: ani.progressPercent,
                      isCompleted: ani.isCompleted,
                    }}
                  />
                </motion.div>
              ),
          )}
        </div>
      </Container>
    </section>
  );
};

export default ContinueWatching;
