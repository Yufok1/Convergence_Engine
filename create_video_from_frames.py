#!/usr/bin/env python3
"""
Combine PNG frames into MP4 video

Usage:
    python create_video_from_frames.py <frames_directory> [output_video.mp4] [--fps 30]

Example:
    python create_video_from_frames.py "C:\Users\Jeff Towers\Downloads" causation_video.mp4 --fps 30
"""

import os
import sys
import subprocess
import glob
from pathlib import Path
import argparse

def find_frames(directory, pattern="causation-frame-*.png"):
    """Find all frame files matching the pattern"""
    frames = sorted(glob.glob(os.path.join(directory, pattern)))
    return frames

def create_video_from_frames(frames, output_path, fps=30):
    """Use FFmpeg to combine frames into MP4 video"""
    
    if not frames:
        print("❌ No frames found!")
        return False
    
    print(f"📹 Found {len(frames)} frames")
    print(f"🎬 Creating video: {output_path}")
    print(f"⚙️  FPS: {fps}")
    
    # Check if FFmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found!")
        print("   Please install FFmpeg:")
        print("   - Windows: Download from https://ffmpeg.org/download.html")
        print("   - Or use: winget install ffmpeg")
        print("   - Or use: choco install ffmpeg")
        return False
    
    # Create temporary file list for FFmpeg
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for frame in frames:
            f.write(f"file '{frame}'\n")
        filelist_path = f.name
    
    try:
        # Use FFmpeg to create video from frames
        # -r: input frame rate (read frames at this rate)
        # -i: input pattern or file list
        # -c:v libx264: use H.264 codec
        # -pix_fmt yuv420p: ensure compatibility
        # -r: output frame rate
        # -y: overwrite output file
        
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-r', str(fps),  # Input frame rate
            '-i', filelist_path,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-r', str(fps),  # Output frame rate
            '-y',  # Overwrite output
            output_path
        ]
        
        print(f"🔄 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"✅ Video created successfully!")
            print(f"   Output: {output_path}")
            print(f"   Size: {file_size:.2f} MB")
            print(f"   Frames: {len(frames)}")
            print(f"   Duration: {len(frames) / fps:.2f} seconds")
            return True
        else:
            print(f"❌ FFmpeg error:")
            print(result.stderr)
            return False
            
    finally:
        # Clean up temp file
        try:
            os.unlink(filelist_path)
        except:
            pass

def main():
    parser = argparse.ArgumentParser(
        description='Combine PNG frames into MP4 video',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find frames in Downloads folder and create video
  python create_video_from_frames.py "C:\\Users\\Jeff Towers\\Downloads"
  
  # Specify output file and FPS
  python create_video_from_frames.py "C:\\Users\\Jeff Towers\\Downloads" output.mp4 --fps 30
  
  # Use specific pattern
  python create_video_from_frames.py . --pattern "frame-*.png" --fps 24
        """
    )
    
    parser.add_argument('directory', 
                       help='Directory containing frame PNG files')
    parser.add_argument('output', 
                       nargs='?',
                       default=None,
                       help='Output video file (default: causation_video_TIMESTAMP.mp4)')
    parser.add_argument('--fps', 
                       type=int, 
                       default=30,
                       help='Frames per second (default: 30)')
    parser.add_argument('--pattern',
                       default='causation-frame-*.png',
                       help='File pattern to match (default: causation-frame-*.png)')
    
    args = parser.parse_args()
    
    # Find frames
    frames = find_frames(args.directory, args.pattern)
    
    if not frames:
        print(f"❌ No frames found in {args.directory} matching pattern '{args.pattern}'")
        print(f"\n💡 Try:")
        print(f"   - Check the directory path")
        print(f"   - List files: dir {args.directory}")
        print(f"   - Use --pattern to match your files")
        return 1
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        timestamp = int(os.path.getmtime(frames[0]))
        output_path = f"causation_video_{timestamp}.mp4"
    
    # Create video
    success = create_video_from_frames(frames, output_path, args.fps)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())

