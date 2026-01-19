import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'

// GET /api/favorites/user/[userId] - Get user's favorite property IDs
export async function GET(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params
    const supabase = await createClient()

    const { data, error } = await supabase
      .from('user_favorites')
      .select('property_id')
      .eq('user_id', userId)

    if (error) throw error

    const propertyIds = data?.map(f => f.property_id) || []
    return NextResponse.json(propertyIds)
  } catch (error: any) {
    console.error('Error fetching favorites:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to fetch favorites' },
      { status: 500 }
    )
  }
}
