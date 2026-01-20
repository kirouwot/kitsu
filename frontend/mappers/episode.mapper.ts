import { Episode } from "@/types/episodes";
import { BackendEpisode, isBackendEpisode } from "./common";
import { assertString, assertNumber, assertOptional, assertArray } from "@/lib/contract-guards";

/**
 * Maps BackendEpisode to Episode
 * PURE function - no fallbacks, no optional chaining
 */
export function mapBackendEpisodeToEpisode(dto: BackendEpisode): Episode {
  assertString(dto.id, "Episode.id");
  assertNumber(dto.number, "Episode.number");

  const title = assertOptional(dto.title, assertString, "Episode.title") ?? `Episode ${dto.number}`;

  return {
    title,
    episodeId: dto.id,
    number: dto.number,
    isFiller: false,
  };
}

/**
 * Maps array of unknown data to Episode array
 * This is the ONLY function that query layer should use for mapping episode arrays
 */
export function mapEpisodeArrayToEpisodeArray(data: unknown): Episode[] {
  assertArray(data, "EpisodeArray");
  return data.map((item) => {
    if (!isBackendEpisode(item)) {
      throw new Error("Invalid episode data in array");
    }
    return mapBackendEpisodeToEpisode(item);
  });
}
