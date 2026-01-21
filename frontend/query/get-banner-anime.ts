import { queryKeys } from "@/constants/query-keys";
import { api } from "@/lib/api";
import { useQuery } from "react-query";

interface IAnimeBanner {
  Media: {
    id: number;
    bannerImage: string;
  };
}

const getAnimeBanner = async (anilistID: number) => {
  try {
    const res = await api.post(
      "https://graphql.anilist.co",
      {
        query: `
      query ($id: Int) {
        Media(id: $id, type: ANIME) {
          id
          bannerImage
        }
      }
    `,
        variables: {
          id: anilistID,
        },
      },
      { timeout: 10000 },
    );
    return res.data.data as IAnimeBanner;
  } catch (error) {
    console.error("Failed to fetch anime banner", error);
    return { Media: { id: anilistID, bannerImage: "" } } as IAnimeBanner;
  }
};

export const useGetAnimeBanner = (anilistID: number) => {
  return useQuery({
    queryFn: () => getAnimeBanner(anilistID),
    queryKey: queryKeys.animeBanner(anilistID),
    enabled: !!anilistID,
    staleTime: 1000 * 60 * 60,
    refetchOnWindowFocus: false,
    retry: false,
  });
};
