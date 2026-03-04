from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import JobSerializer
from .models import Job
from .tasks import run_job


class JobViewSet(viewsets.GenericViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        run_job.delay(str(job.id))
        return Response({'job_id': str(job.id)}, status=202)

    def retrieve(self, request, pk=None):
        job = self.get_object()
        return Response(self.get_serializer(job).data)
