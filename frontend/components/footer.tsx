import React from "react";
import { DiscordLogoIcon, GitHubLogoIcon } from "@radix-ui/react-icons";
import Image from "next/image";
import Link from "next/link";
import Container from "./container";
import { Separator } from "./ui/separator";
import { Button } from "./ui/button";

const Footer = () => {
  return (
    <footer className="border-t border-border bg-card/50 backdrop-blur-sm">
      <Container className="py-12">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Logo и описание */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Image src="/icon.png" width={40} height={40} alt="Kitsune" />
              <span className="text-xl font-bold gradient-text">Kitsune</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Best site for watching anime online
            </p>
          </div>

          {/* Ссылки */}
          <div>
            <h4 className="font-semibold mb-4">Navigation</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <Link href="/" className="hover:text-primary transition-colors">
                  Home
                </Link>
              </li>
              {/* Uncomment when catalog is ready
              <li>
                <Link href="/catalog" className="hover:text-primary transition-colors">
                  Каталог
                </Link>
              </li>
              */}
            </ul>
          </div>

          {/* Информация */}
          <div>
            <h4 className="font-semibold mb-4">Information</h4>
            <p className="text-sm text-muted-foreground">
              Kitsune does not store any files on the server. We only link to media which is hosted on 3rd party services.
            </p>
          </div>

          {/* Соцсети */}
          <div>
            <h4 className="font-semibold mb-4">Community</h4>
            <div className="flex gap-3">
              <a href="https://github.com/Dovakiin0/Kitsune" target="_blank" rel="noopener noreferrer">
                <Button size="icon" variant="outline" className="rounded-full">
                  <GitHubLogoIcon width={20} height={20} />
                </Button>
              </a>
              <a href="https://discord.gg/6yAJ3XDHTt" target="_blank" rel="noopener noreferrer">
                <Button size="icon" variant="outline" className="rounded-full">
                  <DiscordLogoIcon width={20} height={20} />
                </Button>
              </a>
            </div>
          </div>
        </div>

        <Separator className="my-8" />

        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-muted-foreground">
          <p>&copy; 2024 Kitsune. All rights reserved.</p>
          <p>Made with ❤️</p>
        </div>
      </Container>
    </footer>
  );
};

export default Footer;
