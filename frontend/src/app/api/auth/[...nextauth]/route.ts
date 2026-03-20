import NextAuth, { type NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';

const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email', placeholder: 'admin@nigehbaan.org' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        // Placeholder — in production, validate against the backend API
        if (
          credentials?.email === 'admin@nigehbaan.org' &&
          credentials?.password === 'changeme'
        ) {
          return {
            id: '1',
            name: 'Admin',
            email: credentials.email,
          };
        }
        return null;
      },
    }),
  ],
  session: {
    strategy: 'jwt',
    maxAge: 24 * 60 * 60, // 24 hours
  },
  pages: {
    signIn: '/admin',
  },
  secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
