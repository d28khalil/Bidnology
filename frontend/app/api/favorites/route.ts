import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'

// POST /api/favorites - Add to favorites
export async function POST(request: NextRequest) {
  try {
    const { user_id, property_id } = await request.json()

    if (!user_id || !property_id) {
      return NextResponse.json(
        { error: 'user_id and property_id are required' },
        { status: 400 }
      )
    }

    const supabase = await createClient()

    const { error } = await supabase
      .from('user_favorites')
      .insert({ user_id, property_id })

    if (error) {
      // Check if it's a duplicate (unique constraint)
      if (error.code === '23505') {
        return NextResponse.json(
          { error: 'Property already in favorites' },
          { status: 409 }
        )
      }
      throw error
    }

    return NextResponse.json({ message: 'Added to favorites' })
  } catch (error: any) {
    console.error('Error adding favorite:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to add favorite' },
      { status: 500 }
    )
  }
}

// DELETE /api/favorites - Remove from favorites
export async function DELETE(request: NextRequest) {
  try {
    const { user_id, property_id } = await request.json()

    if (!user_id || !property_id) {
      return NextResponse.json(
        { error: 'user_id and property_id are required' },
        { status: 400 }
      )
    }

    const supabase = await createClient()

    const { error } = await supabase
      .from('user_favorites')
      .delete()
      .eq('user_id', user_id)
      .eq('property_id', property_id)

    if (error) throw error

    return NextResponse.json({ message: 'Removed from favorites' })
  } catch (error: any) {
    console.error('Error removing favorite:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to remove favorite' },
      { status: 500 }
    )
  }
}
