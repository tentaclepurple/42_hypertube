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
    
    const resolvedParams = params;
    const movieId = resolvedParams.params[0];
    const subtitlePath = resolvedParams.params.slice(1).join('/');
    
    const backendUrl = `http://backend:8000/api/v1/movies/${movieId}/subtitles/${subtitlePath}?torrent_hash=${torrentHash}`;

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Cookie': request.headers.get('cookie') || '',
        'User-Agent': request.headers.get('user-agent') || 'NextJS-Proxy',
      },
    });
    
    if (!response.ok) {
      return new NextResponse(`Backend error: ${response.status}`, { 
        status: response.status 
      });
    }
    
    const subtitleContent = await response.text();
    
    const contentType = getSubtitleContentType(subtitlePath);
    
    return new NextResponse(subtitleContent, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': 'inline',
        'Cache-Control': 'public, max-age=3600',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });
    
  } catch {
    return new NextResponse('Internal server error', { status: 500 });
  }
}

export async function OPTIONS(){
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
}

function getSubtitleContentType(filename: string): string {
  const ext = filename.toLowerCase().split('.').pop();
  
  const mimeTypes: { [key: string]: string } = {
    'srt': 'text/srt; charset=utf-8',
    'vtt': 'text/vtt; charset=utf-8',
    'sub': 'text/plain; charset=utf-8',
    'ass': 'text/x-ssa; charset=utf-8',
    'ssa': 'text/x-ssa; charset=utf-8',
    'sbv': 'text/plain; charset=utf-8'
  };
  
  return mimeTypes[ext || 'srt'] || 'text/srt; charset=utf-8';
}