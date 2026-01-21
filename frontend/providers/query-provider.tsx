"use client";

import React, { ReactNode, useState } from "react";
import { QueryClient, QueryClientProvider } from "react-query";

type Props = {
  children: ReactNode;
};

const DEFAULT_STALE_TIME = 1000 * 60 * 5;
const DEFAULT_CACHE_TIME = 1000 * 60 * 10;
const DEFAULT_RETRY_COUNT = 1;

const QueryProvider = (props: Props) => {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: DEFAULT_STALE_TIME,
            cacheTime: DEFAULT_CACHE_TIME,
            refetchOnWindowFocus: false,
            retry: DEFAULT_RETRY_COUNT,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {props.children}
    </QueryClientProvider>
  );
};

export default QueryProvider;
