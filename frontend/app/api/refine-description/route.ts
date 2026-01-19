import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'

export async function POST(request: NextRequest) {
  try {
    const { property_id, description } = await request.json()

    if (!description) {
      return NextResponse.json(
        { error: 'Description is required' },
        { status: 400 }
      )
    }

    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) {
      return NextResponse.json(
        { error: 'OpenAI API key not configured' },
        { status: 500 }
      )
    }

    // Dynamically import OpenAI to avoid build-time initialization
    const OpenAI = (await import('openai')).default
    const openai = new OpenAI({ apiKey })

    // Call GPT-4o-mini to refine the description while maintaining accuracy
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: `You are a real estate description editor. Your task is to refine property auction descriptions to make them clearer and more readable while maintaining strict accuracy.

CRITICAL RULES:
1. Keep all factual information exactly as provided (addresses, dates, monetary amounts, legal parties, case numbers)
2. Improve readability through better organization and clearer language
3. Do NOT add any information that isn't in the original description
4. Do NOT remove important details
5. Maintain a professional, business-appropriate tone
6. Organize information logically (e.g., property details, auction terms, legal information)
7. Use clear headings and bullet points where appropriate
8. Do NOT use markdown formatting (no ** for bold, no ## for headings) - use plain text with line breaks and hyphens for bullets

Output ONLY the refined description text, no preamble or explanation.`,
        },
        {
          role: 'user',
          content: `Please refine this property auction description while maintaining all factual accuracy:\n\n${description}`,
        },
      ],
      temperature: 0.3, // Lower temperature for more consistent, accurate output
      max_tokens: 2000,
    })

    const refined_description = completion.choices[0]?.message?.content || description

    // Save the refined description to the database for future use
    const supabase = await createClient()
    const { error: saveError } = await supabase
      .from('foreclosure_listings')
      .update({ refined_description })
      .eq('id', property_id)

    if (saveError) {
      console.error('Error saving refined description to database:', saveError)
      // Continue anyway - we'll still return the refined description
    }

    return NextResponse.json({
      refined_description,
      property_id,
    })
  } catch (error: any) {
    console.error('Error refining description:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to refine description' },
      { status: 500 }
    )
  }
}
