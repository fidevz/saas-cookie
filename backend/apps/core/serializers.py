"""
Core app serializers.
"""

from rest_framework import serializers


class SupportSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=500)
    message = serializers.CharField(max_length=5000)
