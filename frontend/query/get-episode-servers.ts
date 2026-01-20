import { queryKeys } from "@/constants/query-keys";
import { IEpisodeServers } from "@/types/episodes";
import { useQuery } from "react-query";
import { api } from "@/lib/api";
import { assertApiSuccessResponse } from "@/lib/contract-guards";

const getEpisodeServers = async (episodeId: string) => {
  const fallback: IEpisodeServers = {
    episodeId: "",
    episodeNo: "",
    sub: [],
    dub: [],
    raw: [],
  };

  if (!episodeId) return fallback;

  const res = await api.get("/api/episode/servers", {
      params: {
        animeEpisodeId: decodeURIComponent(episodeId),
      },
    timeout: 10000,
  });
  
  assertApiSuccessResponse(res.data);
  
  if (!res.data.data) {
    throw new Error("Contract violation: episode servers response missing data field");
  }
  
  return res.data.data as IEpisodeServers;
};

export const useGetEpisodeServers = (episodeId: string) => {
  return useQuery({
    queryFn: () => getEpisodeServers(episodeId),
    queryKey: queryKeys.episodeServers(episodeId),
    refetchOnWindowFocus: false,
    staleTime: 1000 * 60 * 3,
    enabled: Boolean(episodeId),
    retry: false,
  });
};
