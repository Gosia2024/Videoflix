from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from django.conf import settings
from django.http import FileResponse, Http404

from .models import Video
from .serializers import VideoSerializer

import os

from .tasks import convert_video_to_hls


# ==========================================
# 📺 VIDEO LIST
# GET /api/video/
# ==========================================

class VideoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = Video.objects.all().order_by("-created_at")

        serializer = VideoSerializer(
            videos,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


# ==========================================
# 🎬 HLS MANIFEST
# GET /api/video/<movie_id>/<resolution>/index.m3u8
# ==========================================

class VideoManifestView(APIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]
    def get(self, request, movie_id, resolution):

        # 1️⃣ sprawdź czy video istnieje w DB
        try:
            Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")

        # 2️⃣ ścieżka do pliku
        manifest_path = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            str(movie_id),
            resolution,
            "index.m3u8"
        )

        # 3️⃣ sprawdź czy istnieje
        if not os.path.exists(manifest_path):
            raise Http404("Manifest not found")

        # 4️⃣ zwróć plik
        return FileResponse(
            open(manifest_path, "rb"),
            content_type="application/vnd.apple.mpegurl"
        )


# ==========================================
# 🎞 HLS SEGMENT
# GET /api/video/<movie_id>/<resolution>/<segment>/
# ==========================================

class VideoSegmentView(APIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def get(self, request, movie_id, resolution, segment):

        # 1️⃣ sprawdź czy video istnieje
        try:
            Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")

        # 🔒 zabezpieczenie przed path traversal
        if not segment.endswith(".ts"):
            raise Http404("Invalid segment")

        # 2️⃣ buduj ścieżkę
        segment_path = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            str(movie_id),
            resolution,
            segment
        )

        # 3️⃣ sprawdź czy plik istnieje
        if not os.path.exists(segment_path):
            raise Http404("Segment not found")

        # 4️⃣ zwróć plik .ts
        return FileResponse(
            open(segment_path, "rb"),
            content_type="video/MP2T"
        )
