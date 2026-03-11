'use client'

import { SignUp } from '@clerk/nextjs';

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Join Gen-Friend
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Start your productivity journey
          </p>
        </div>
        <SignUp
          appearance={{
            elements: {
              rootBox: "mx-auto",
              card: "bg-white dark:bg-gray-800 shadow-xl rounded-lg",
            }
          }}
        />
      </div>
    </div>
  );
}
