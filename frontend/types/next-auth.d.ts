import type { DefaultSession } from "next-auth";

import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    user: DefaultSession["user"] & {
      id: string;
      authProvider?: string;
      authProviderAccountId?: string;
      isEmailVerified: boolean;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    userId?: string;
    authProvider?: string;
    authProviderAccountId?: string;
    isEmailVerified?: boolean;
  }
}
