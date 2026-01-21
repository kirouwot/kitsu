"use client";

import Link from "next/link";
import Image from "next/image";
import { cn } from "@/lib/utils";

import Container from "./container";
import { Separator } from "./ui/separator";

import { nightTokyo } from "@/utils/fonts";
import { ROUTES } from "@/constants/routes";
import { ReactNode, useState } from "react";

import SearchBar from "./search-bar";
import { MenuIcon, X } from "lucide-react";
import useScrollPosition from "@/hooks/use-scroll-position";
import { Sheet, SheetClose, SheetContent, SheetTrigger } from "./ui/sheet";
import LoginPopoverButton from "./login-popover-button";
import { useAuthSelector } from "@/store/auth-store";
import NavbarAvatar from "./navbar-avatar";
import { ThemeToggle } from "./theme-toggle";

const menuItems: Array<{ title: string; href?: string }> = [
  {
    title: "Home",
    href: ROUTES.HOME,
  },
  // {
  //   title: "Catalog",
  // },
  // {
  //   title: "Schedule",
  // },
  // {
  //   title: "Random",
  // },
];

const NavBar = () => {
  const auth = useAuthSelector((state) => state.auth);
  const clearAuth = useAuthSelector((state) => state.clearAuth);
  const { y } = useScrollPosition();
  const isHeaderSticky = y > 0;

  return (
    <nav
      className={cn([
        "fixed top-0 w-full z-[100] transition-all duration-300",
        isHeaderSticky
          ? "backdrop-blur-xl bg-black/80 dark:bg-black/80"
          : "bg-transparent",
      ])}
    >
      <Container className="flex items-center justify-between h-16">
        {/* ЛЕВАЯ ЧАСТЬ: Лого + Меню */}
        <div className="flex items-center gap-8">
          <Link
            href={ROUTES.HOME}
            className="flex items-center gap-2 cursor-pointer"
          >
            <Image
              src="/icon.png"
              alt="logo"
              width={40}
              height={40}
              priority
              suppressHydrationWarning
            />
            <h1
              className={cn([
                nightTokyo.className,
                "text-xl font-bold gradient-text tracking-wider",
              ])}
            >
              Kitsune
            </h1>
          </Link>
          
          {/* Desktop Menu */}
          <div className="hidden lg:flex items-center gap-6">
            {menuItems.map((menu, idx) => (
              <Link 
                href={menu.href || "#"} 
                key={idx}
                className="text-sm font-medium transition-colors hover:text-primary relative group"
              >
                {menu.title}
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
              </Link>
            ))}
          </div>
        </div>

        {/* ПРАВАЯ ЧАСТЬ: Поиск + Тема + Профиль */}
        <div className="hidden lg:flex items-center gap-4">
          <SearchBar />
          <ThemeToggle />
          {auth ? (
            <NavbarAvatar auth={auth} clearAuth={clearAuth} />
          ) : (
            <LoginPopoverButton />
          )}
        </div>

        {/* Mobile Menu */}
        <div className="lg:hidden flex items-center gap-3">
          <ThemeToggle />
          <MobileMenuSheet trigger={<MenuIcon suppressHydrationWarning />} />
          {auth ? (
            <NavbarAvatar auth={auth} clearAuth={clearAuth} />
          ) : (
            <LoginPopoverButton />
          )}
        </div>
      </Container>
    </nav>
  );
};

const MobileMenuSheet = ({ trigger }: { trigger: ReactNode }) => {
  const [open, setOpen] = useState<boolean>(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger>{trigger}</SheetTrigger>
      <SheetContent
        className="flex flex-col w-[80vw] z-[150]"
        hideCloseButton
        onOpenAutoFocus={(e) => e.preventDefault()}
        onCloseAutoFocus={(e) => e.preventDefault()}
      >
        <div className="w-full h-full relative">
          <SheetClose className="absolute top-0 right-0">
            <X />
          </SheetClose>
          <div className="flex flex-col gap-5 mt-10">
            {menuItems.map((menu, idx) => (
              <Link
                href={menu.href || "#"}
                key={idx}
                onClick={() => setOpen(false)}
                className="text-lg font-medium hover:text-primary transition-colors"
              >
                {menu.title}
              </Link>
            ))}
            <Separator />
            <SearchBar onAnimeClick={() => setOpen(false)} />
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default NavBar;
