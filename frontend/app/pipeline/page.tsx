'use client'

import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { KanbanColumn } from '@/components/KanbanColumn'

// Mock data
const kanbanData = {
  new: [
    {
      id: '1',
      address: '1240 Willow Creek Ln',
      city: 'Sacramento',
      state: 'CA',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAR5ezaTNWPYsdE_h-boeQ0WvAWBqRRjMKBG4qdYFWlnOeigYzQyfu4wcZZ5N0_7HLNTGQzncbLPBgOdGCT3WLsP4xjenRg9OG4Y2X7rhdOPtbkuAKLLt0EzWFrZd-70WuTW6C0DNviySiL9ffYvN_nrSJH3aEqE0VejqNF_qg66T1OhBC1-9x3pJFcKLKu5_WxSoMx85v-QgXzptLj5FuRS71yP5xkCZbmgWlsV8jSI628FQ_E0-_2Eq_vBEmrCEdo6PVBTVp3',
      openingBid: 245000,
      estimatedARV: 420000,
      auctionDate: 'Today, 2:00 PM',
      tags: ['High Equity'],
    },
    {
      id: '2',
      address: '8502 Ocean View Blvd',
      city: 'San Diego',
      state: 'CA',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAvQsw05HGTr8tKQaK9I2Yg-iFxVhYZmU4bOlcuezVlTrzcxWuj3NUZ2yeR7cm2jtGozuHovDSkAA94XWDEsOZY_3sWsmSD4q-KR9ixdUvs_HDsRWxelP6Eh6mjGPJmDSsGpfVi0ouxbCQn0Tt4wfBeYlrhGGNzWK-GqPFMNaklCh509jtHfD3lgEwQbUqFk8kPi9DqbLUS1VvM2vHF1NAo3jswsMaLyZNFcNZolCcz6rP3w-08bs_7d6Uqe_caBSfxL7aj5EWR',
      openingBid: 580000,
      estimatedARV: 710000,
      auctionDate: 'Oct 24, 10:00 AM',
      tags: ['Beach Area'],
    },
  ],
  researching: [
    {
      id: '3',
      address: '4409 Maplewood Ave',
      city: 'Los Angeles',
      state: 'CA',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAVM52CyBZKuKXHcqVyiDcUyNLdqFVF4nNRWogdZLs8qtKnLyb-SZrHkSEreaDQc8j0wJJV73-OpTB0fHEOimzlz243O0fY4uPyZELWZ5FK7NwsGfqfpAGBKluI6pI-e_K7ls3klffgERuwkAB-96b5-CFvxV7S123KJS4YBXJdTe5xlS1aCcFVWXQbZcbjNrGhKzYfhR-rmYToUc-5EtmwGLBjwQQi-sq9ztG-AM15hVVKxMDFN3oyOf1Bt-16nJ7DJp1rZYwx',
      openingBid: 890000,
      estimatedARV: 950000,
      auctionDate: 'Oct 25, 09:30 AM',
      tags: ['Title Search'],
    },
  ],
  'under-contract': [
    {
      id: '4',
      address: '772 Pine Ridge Dr',
      city: 'Roseville',
      state: 'CA',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDtsNaovPtiNUomCKgIxgGH0Dg0tXdXcFgFxeK62fkaaWGQOrt-4UiiLDJSrimoFtwcMSmn38YLvDX6SEcaBWxULDFmn-ffalC4l58kzUJ-AGOg0F-AKugf00O7DS3xUkb4gR0XqFFcTkVGxsYOlAQxk_Du11s4J3B6Tq87UowQbr8ix1feIzC9PihttFEzCkqxqwtWWtUa6Av_xtKRx424SiLwGRsSaO-0gYr_Oq0gE5kR7c2rUHf5WdR7v3eIxp4XfSktEuG9',
      openingBid: 310000,
      estimatedARV: 480000,
      auctionDate: 'Oct 26, 11:00 AM',
      tags: ['Pending'],
    },
  ],
  closed: [
    {
      id: '5',
      address: '2020 Elm Street',
      city: 'Modesto',
      state: 'CA',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCRyhjaJ6dWrTC79mzNywH2DL9OC7S8jtRJp2XOSlPg5EwFaaGjP2iA7rSzgjK9MK77wwCfNpSQk81IgMAmRoVGPkQ7omJOPSw21DZ2tR3onywACEKIzDWDeaTv1xM5Fl9Yz6zfHGV7W_hChHuEfxJgQsqIOxicaFQV1pGwnlU-UmUDHtOpPmPrN0LYqQb0L5K1t7SFY5pBxc50Hp8tD8zQuSzvGi8yv1NbpkIC5b0rSS4bOOU0k-3F9R7McdsKulPH1dLnxbyM',
      openingBid: 185000,
      estimatedARV: 290000,
      auctionDate: 'Closed Oct 20',
      tags: ['Won $185K'],
    },
  ],
}

export default function PipelinePage() {
  return (
    <div className="h-screen flex overflow-hidden">
      {/* V2: Restore for V2 <Sidebar /> */}

      <main className="flex-1 flex flex-col h-full relative overflow-hidden">
        <Header />

        {/* Kanban Board */}
        <div className="flex-1 overflow-x-auto p-6 bg-background-dark">
          <div className="flex gap-4 h-full min-w-max">
            <KanbanColumn
              title="New Opportunities"
              count={kanbanData.new.length}
              status="new"
              properties={kanbanData.new}
            />
            <KanbanColumn
              title="Researching"
              count={kanbanData.researching.length}
              status="researching"
              properties={kanbanData.researching}
            />
            <KanbanColumn
              title="Under Contract"
              count={kanbanData['under-contract'].length}
              status="under-contract"
              properties={kanbanData['under-contract']}
            />
            <KanbanColumn
              title="Closed / Won"
              count={kanbanData.closed.length}
              status="closed"
              properties={kanbanData.closed}
            />
          </div>
        </div>
      </main>
    </div>
  )
}
