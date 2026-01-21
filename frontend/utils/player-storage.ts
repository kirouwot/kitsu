"use client";

import { getLocalStorageJSON, setLocalStorageJSON } from "@/utils/storage";

export type PlayerStorage = {
  lastEpisode?: number;
  lastTranslation?: string;
  autoplayNext?: boolean;
  positionSeconds?: number;
  progressPercent?: number;
  syncedToServer?: boolean;
  updatedAt?: number;
};

const storageCache = new Map<string, PlayerStorage>();
const MILLISECONDS_IN_SECOND = 1000;

export const getPlayerStorageKey = (animeId: string) => `player:${animeId}`;

const normalizeStorage = (value: PlayerStorage): PlayerStorage => ({
  lastEpisode: typeof value.lastEpisode === "number" ? value.lastEpisode : undefined,
  lastTranslation:
    typeof value.lastTranslation === "string" ? value.lastTranslation : undefined,
  autoplayNext:
    typeof value.autoplayNext === "boolean" ? value.autoplayNext : undefined,
  positionSeconds:
    typeof value.positionSeconds === "number" ? value.positionSeconds : undefined,
  progressPercent:
    typeof value.progressPercent === "number" ? value.progressPercent : undefined,
  syncedToServer:
    typeof value.syncedToServer === "boolean" ? value.syncedToServer : undefined,
  updatedAt: typeof value.updatedAt === "number" ? value.updatedAt : undefined,
});

export const getPlayerStorage = (animeId: string): PlayerStorage => {
  if (!animeId) return {};
  const key = getPlayerStorageKey(animeId);
  const cached = storageCache.get(key);
  if (cached) return cached;
  const stored = normalizeStorage(getLocalStorageJSON<PlayerStorage>(key, {}));
  storageCache.set(key, stored);
  return stored;
};

export const updatePlayerStorage = (
  animeId: string,
  update: Partial<PlayerStorage>,
): PlayerStorage => {
  if (!animeId) return {};
  const key = getPlayerStorageKey(animeId);
  const next: PlayerStorage = {
    ...getPlayerStorage(animeId),
    ...update,
    updatedAt: Math.floor(Date.now() / MILLISECONDS_IN_SECOND),
  };
  storageCache.set(key, next);
  setLocalStorageJSON(key, next);
  return next;
};
