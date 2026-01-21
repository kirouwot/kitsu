"use client";

import ContinueWatching from "@/components/continue-watching";
import FeaturedCollection from "@/components/featured-collection";
import { useGetHomePageData } from "@/query/get-home-page-data";
import { IAnime, LatestCompletedAnime, SpotlightAnime } from "@/types/anime";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

// Dynamically import components
const HeroSection = dynamic(() => import("@/components/hero-section"));
const LatestEpisodesAnime = dynamic(
  () => import("@/components/latest-episodes-section"),
);
const AnimeSchedule = dynamic(() => import("@/components/anime-schedule"));
const AnimeSections = dynamic(() => import("@/components/anime-sections"));

export default function Home() {
  const [shouldLoadHomeData, setShouldLoadHomeData] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return; // Skip during SSR
    const trigger = () => setShouldLoadHomeData(true);
    const timeoutId = window.setTimeout(trigger, 100);
    return () => window.clearTimeout(timeoutId);
  }, []);

  const { data, isLoading } = useGetHomePageData({
    enabled: shouldLoadHomeData,
  });
  const isHomeDataPending = !shouldLoadHomeData || isLoading || !data;

    return (
    <div className="flex flex-col bg-[#121212]">
      <ContinueWatching />
      <HeroSection
        spotlightAnime={data?.spotlightAnimes as SpotlightAnime[]}
        isDataLoading={isHomeDataPending}
      />
      <LatestEpisodesAnime
        loading={isHomeDataPending}
        latestEpisodes={data?.latestEpisodeAnimes as LatestCompletedAnime[]}
      />

      <FeaturedCollection
        loading={isHomeDataPending}
        featuredAnime={[
          {
            title: "Most Favorite Anime",
            anime: data?.mostFavoriteAnimes as IAnime[],
          },
          {
            title: "Most Popular Anime",
            anime: data?.mostPopularAnimes as IAnime[],
          },
          {
            title: "Latest Completed Anime",
            anime: data?.latestCompletedAnimes as LatestCompletedAnime[],
          },
        ]}
      />
      <AnimeSections
        title={"Trending Anime"}
        trendingAnime={data?.trendingAnimes as IAnime[]}
        loading={isHomeDataPending}
      />

      <AnimeSchedule />

      <AnimeSections
        title={"Upcoming Animes"}
        trendingAnime={data?.topUpcomingAnimes as IAnime[]}
        loading={isHomeDataPending}
      />
    </div>
  );
}
