import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { params: string[] } }
) {
  try {
    const { searchParams } = new URL(request.url);
    const torrentHash = searchParams.get('torrent_hash');
    
    if (!torrentHash) {
      return new NextResponse('Missing torrent_hash parameter', { status: 400 });
    }
    
    // Awaitar params antes de usarlo
    const resolvedParams = await params;
    const movieId = resolvedParams.params[0];
    const subtitlePath = resolvedParams.params.slice(1).join('/');
    
    const backendUrl = `http://backend:8000/api/v1/movies/${movieId}/subtitles/${subtitlePath}?torrent_hash=${torrentHash}`;
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Cookie': request.headers.get('cookie') || '',
      },
    });
    
    if (!response.ok) {
      return new NextResponse(`Backend error: ${response.status}`, { 
        status: response.status 
      });
    }
    
    const subtitleContent = await response.arrayBuffer();
    
    return new NextResponse(subtitleContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/srt',
        'Content-Disposition': 'inline',
        'Cache-Control': 'public, max-age=3600',
      },
    });
    
  } catch (error) {
    console.error('Error in subtitle proxy:', error);
    return new NextResponse('Internal server error', { status: 500 });
  }
}