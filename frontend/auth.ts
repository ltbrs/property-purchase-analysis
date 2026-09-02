import { createHash } from "node:crypto";

import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

const UUID_DNS_NAMESPACE = Buffer.from(
  "6ba7b8109dad11d180b400c04fd430c8",
  "hex",
);

function googleAccountIdToUserId(accountId: string) {
  const bytes = createHash("sha1")
    .update(UUID_DNS_NAMESPACE)
    .update(`acquora:google:${accountId}`)
    .digest()
    .subarray(0, 16);

  bytes[6] = (bytes[6] & 0x0f) | 0x50;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;

  const value = bytes.toString("hex");
  return [
    value.slice(0, 8),
    value.slice(8, 12),
    value.slice(12, 16),
    value.slice(16, 20),
    value.slice(20),
  ].join("-");
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
  providers: [Google],
  pages: {
    signIn: "/connexion",
    error: "/connexion",
  },
  callbacks: {
    jwt({ token, account, profile }) {
      if (account?.provider === "google") {
        token.userId = googleAccountIdToUserId(account.providerAccountId);
      }
      if (account) {
        token.authProvider = account.provider;
        token.authProviderAccountId = account.providerAccountId;
        token.isEmailVerified = profile?.email_verified === true;
      }
      return token;
    },
    session({ session, token }) {
      if (session.user && typeof token.userId === "string") {
        session.user.id = token.userId;
        session.user.authProvider = token.authProvider;
        session.user.authProviderAccountId = token.authProviderAccountId;
        session.user.isEmailVerified = token.isEmailVerified === true;
      }
      return session;
    },
  },
});
