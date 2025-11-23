import NextAuth from "next-auth"
import GoogleProvider from "next-auth/providers/google"

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      // When user signs in with Google, send the token to our backend
      if (account?.provider === "google" && account?.id_token) {
        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
          const response = await fetch(`${apiUrl}/api/auth/google`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              token: account.id_token,
            }),
          })

          if (response.ok) {
            const data = await response.json()
            // Store the JWT token in the session
            account.access_token = data.access_token
            return true
          } else if (response.status === 403) {
            // User email not whitelisted
            const error = await response.json()
            console.error("Access denied:", error.detail)
            return false
          }
        } catch (error) {
          console.error("Backend authentication error:", error)
          return false
        }
      }
      return true
    },
    async jwt({ token, account, user }) {
      // Initial sign in
      if (account && user) {
        return {
          ...token,
          accessToken: account.access_token,
          user: {
            email: user.email,
            name: user.name,
            image: user.image,
          },
        }
      }
      return token
    },
    async session({ session, token }) {
      // Send properties to the client
      if (token.user && typeof token.user === 'object') {
        session.user = token.user as any
      }
      return {
        ...session,
        accessToken: token.accessToken,
      } as any
    },
  },
  pages: {
    signIn: "/login",
  },
})

export { handler as GET, handler as POST }
