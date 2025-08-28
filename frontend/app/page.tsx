'use client';

import HeaderNav from '@/components/HeaderNav';
import ChatInterface from '@/components/ChatInterface';

export default function Page() {
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <HeaderNav signOut={() => {}} />
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <ChatInterface />
      </div>
    </div>
  );
}
