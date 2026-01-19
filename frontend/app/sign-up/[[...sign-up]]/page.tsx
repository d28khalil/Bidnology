import { SignUp } from '@clerk/nextjs'

export default function Page() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center px-4 bg-[#0F1621]">
      <div className="w-full max-w-md">
        <SignUp
          appearance={{
            elements: {
              rootBox: 'bg-[#0F1621]',
              card: 'bg-[#1a2332] border border-gray-800 shadow-2xl',
              headerTitle: 'text-white text-2xl font-bold',
              headerSubtitle: 'text-gray-400',
              socialButtonsBlockButton: 'bg-[#2B6CEE] hover:bg-[#2355c4] text-white border-0',
              dividerRow: 'border-gray-700',
              dividerText: 'text-gray-500',
              formFieldLabel: 'text-gray-300',
              formFieldInput: 'bg-[#0F1621] border-gray-700 text-white focus:ring-2 focus:ring-[#2B6CEE]',
              formFieldAction: 'text-[#2B6CEE] hover:text-[#5a8ff0]',
              footerActionLink: 'text-[#2B6CEE] hover:text-[#5a8ff0]',
              identityPreviewText: 'text-gray-300',
              identityPreviewEditButton: 'text-[#2B6CEE] hover:text-[#5a8ff0]',
              formButtonPrimary: 'bg-[#2B6CEE] hover:bg-[#2355c4] text-white font-medium',
              formButtonSecondary: 'bg-transparent border-gray-700 text-white hover:bg-gray-800',
              alert: 'bg-gray-800 border-gray-700 text-white',
              navbar: 'bg-[#0F1621] border-b border-gray-800',
            },
          }}
        />
      </div>
    </div>
  )
}
